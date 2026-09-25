"""Batch prediction and task-selection protocol tests."""


import json

from leanimum.run.benchmarks.reuf2f import filter_instances, remove_from_preds_file, update_preds_file


def test_filter_instances_no_filters():
    """Test filter_instances with no filtering applied"""
    instances = [{"instance_id": "repo1__test1"}, {"instance_id": "repo2__test2"}, {"instance_id": "repo3__test3"}]
    result = filter_instances(instances, filter_spec="", slice_spec="")
    assert result == instances


def test_filter_instances_regex_filter():
    """Test filter_instances with regex filtering"""
    instances = [
        {"instance_id": "django__test1"},
        {"instance_id": "flask__test2"},
        {"instance_id": "django__test3"},
        {"instance_id": "requests__test4"},
    ]
    result = filter_instances(instances, filter_spec=r"django__.*", slice_spec="")
    expected = [{"instance_id": "django__test1"}, {"instance_id": "django__test3"}]
    assert result == expected


def test_filter_instances_slice_only():
    """Test filter_instances with slice specification"""
    instances = [{"instance_id": f"repo{i}__test{i}"} for i in range(10)]
    result = filter_instances(instances, filter_spec="", slice_spec="2:5")
    expected = [{"instance_id": "repo2__test2"}, {"instance_id": "repo3__test3"}, {"instance_id": "repo4__test4"}]
    assert result == expected


def test_filter_instances_slice_start_only():
    """Test filter_instances with slice start only"""
    instances = [{"instance_id": f"repo{i}__test{i}"} for i in range(5)]
    result = filter_instances(instances, filter_spec="", slice_spec="3:")
    expected = [{"instance_id": "repo3__test3"}, {"instance_id": "repo4__test4"}]
    assert result == expected


def test_filter_instances_slice_end_only():
    """Test filter_instances with slice end only"""
    instances = [{"instance_id": f"repo{i}__test{i}"} for i in range(5)]
    result = filter_instances(instances, filter_spec="", slice_spec=":2")
    expected = [{"instance_id": "repo0__test0"}, {"instance_id": "repo1__test1"}]
    assert result == expected


def test_filter_instances_filter_and_slice():
    """Test filter_instances with both filtering and slicing"""
    instances = [
        {"instance_id": "django__test1"},
        {"instance_id": "flask__test2"},
        {"instance_id": "django__test3"},
        {"instance_id": "django__test4"},
        {"instance_id": "requests__test5"},
    ]
    result = filter_instances(instances, filter_spec=r"django__.*", slice_spec="1:3")
    expected = [{"instance_id": "django__test3"}, {"instance_id": "django__test4"}]
    assert result == expected


def test_filter_instances_shuffle():
    """Test filter_instances with shuffle enabled produces deterministic results"""
    instances = [{"instance_id": f"repo{i:02d}__test{i}"} for i in range(10)]
    # Test that shuffle produces same result with same seed
    result1 = filter_instances(instances.copy(), filter_spec="", slice_spec="", shuffle=True)
    result2 = filter_instances(instances.copy(), filter_spec="", slice_spec="", shuffle=True)
    assert result1 == result2
    # Test that shuffled result is different from original order
    result_no_shuffle = filter_instances(instances.copy(), filter_spec="", slice_spec="", shuffle=False)
    assert result1 != result_no_shuffle


def test_filter_instances_empty_list():
    """Test filter_instances with empty input list"""
    result = filter_instances([], filter_spec=r".*", slice_spec="0:5", shuffle=True)
    assert result == []


def test_filter_instances_no_matches():
    """Test filter_instances when regex matches nothing"""
    instances = [{"instance_id": "django__test1"}, {"instance_id": "flask__test2"}]
    result = filter_instances(instances, filter_spec=r"nonexistent__.*", slice_spec="")
    assert result == []


def test_update_preds_file_new_file(tmp_path):
    """Test update_preds_file when output file doesn't exist"""
    output_path = tmp_path / "preds.json"
    update_preds_file(output_path, "test__instance__1", "test_model", "test_result")

    assert output_path.exists()
    result = json.loads(output_path.read_text())
    expected = {
        "test__instance__1": {
            "model_name_or_path": "test_model",
            "instance_id": "test__instance__1",
            "model_patch": "test_result",
        }
    }
    assert result == expected


def test_update_preds_file_existing_file(tmp_path):
    """Test update_preds_file when output file already exists"""
    output_path = tmp_path / "preds.json"

    # Create initial file with one instance
    initial_data = {
        "existing__instance": {
            "model_name_or_path": "old_model",
            "instance_id": "existing__instance",
            "model_patch": "old_result",
        }
    }
    output_path.write_text(json.dumps(initial_data))

    # Add new instance
    update_preds_file(output_path, "new__instance", "new_model", "new_result")

    result = json.loads(output_path.read_text())
    expected = {
        "existing__instance": {
            "model_name_or_path": "old_model",
            "instance_id": "existing__instance",
            "model_patch": "old_result",
        },
        "new__instance": {
            "model_name_or_path": "new_model",
            "instance_id": "new__instance",
            "model_patch": "new_result",
        },
    }
    assert result == expected


def test_update_preds_file_overwrite_existing(tmp_path):
    """Test update_preds_file overwrites existing instance"""
    output_path = tmp_path / "preds.json"

    # Create initial file
    initial_data = {
        "test__instance": {
            "model_name_or_path": "old_model",
            "instance_id": "test__instance",
            "model_patch": "old_result",
        }
    }
    output_path.write_text(json.dumps(initial_data))

    # Update existing instance
    update_preds_file(output_path, "test__instance", "new_model", "new_result")

    result = json.loads(output_path.read_text())
    expected = {
        "test__instance": {
            "model_name_or_path": "new_model",
            "instance_id": "test__instance",
            "model_patch": "new_result",
        }
    }
    assert result == expected


def test_remove_from_preds_file_existing(tmp_path):
    """Test remove_from_preds_file removes existing instance"""
    output_path = tmp_path / "preds.json"

    # Create file with multiple instances
    initial_data = {
        "instance1": {"model_name_or_path": "model1", "instance_id": "instance1", "model_patch": "result1"},
        "instance2": {"model_name_or_path": "model2", "instance_id": "instance2", "model_patch": "result2"},
    }
    output_path.write_text(json.dumps(initial_data))

    # Remove one instance
    remove_from_preds_file(output_path, "instance1")

    result = json.loads(output_path.read_text())
    expected = {"instance2": {"model_name_or_path": "model2", "instance_id": "instance2", "model_patch": "result2"}}
    assert result == expected


def test_remove_from_preds_file_nonexistent_instance(tmp_path):
    """Test remove_from_preds_file with nonexistent instance"""
    output_path = tmp_path / "preds.json"

    initial_data = {"instance1": {"model_name_or_path": "model1", "instance_id": "instance1", "model_patch": "result1"}}
    output_path.write_text(json.dumps(initial_data))

    # Try to remove nonexistent instance
    remove_from_preds_file(output_path, "nonexistent")

    # File should be unchanged
    result = json.loads(output_path.read_text())
    assert result == initial_data


def test_remove_from_preds_file_no_file(tmp_path):
    """Test remove_from_preds_file when file doesn't exist"""
    output_path = tmp_path / "preds.json"

    # Should not raise an error
    remove_from_preds_file(output_path, "any_instance")

    # File should still not exist
    assert not output_path.exists()
