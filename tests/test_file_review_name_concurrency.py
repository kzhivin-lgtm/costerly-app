import pytest

from use_cases.rfq_processing import FileReviewNameConflict, save_file_review_object_name


def test_file_review_name_save_requires_the_observed_prior_name(monkeypatch):
    updates = []
    audits = []
    client = object()
    monkeypatch.setattr("use_cases.rfq_processing.get_supabase_client", lambda: client)
    monkeypatch.setattr(
        "use_cases.rfq_processing.rename_file_review_object_if_unchanged",
        lambda actual_client, **kwargs: updates.append((actual_client, kwargs)) or True,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing._queue_object_name_write_audit",
        lambda **kwargs: audits.append(kwargs),
    )

    saved_name = save_file_review_object_name(
        run_id="run-001",
        object_id="object-001",
        object_name="  Reception desk  ",
        expected_name="Object 1",
    )

    assert saved_name == "Reception desk"
    assert updates == [(
        client,
        {
            "company_id": "001",
            "run_id": "run-001",
            "object_id": "object-001",
            "expected_name": "Object 1",
            "object_name": "Reception desk",
        },
    )]
    assert audits == [{
        "company_id": "001",
        "run_id": "run-001",
        "object_id": "object-001",
        "expected_name": "Object 1",
        "requested_name": "Reception desk",
        "write_source": "file_review_inline",
    }]


def test_file_review_name_rejects_a_stale_placeholder(monkeypatch):
    client = object()
    monkeypatch.setattr("use_cases.rfq_processing.get_supabase_client", lambda: client)
    monkeypatch.setattr(
        "use_cases.rfq_processing.rename_file_review_object_if_unchanged",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.fetch_rfq_detected_object_names",
        lambda *_args, **_kwargs: [{"object_id": "object-001", "object_name": "Storage bench"}],
    )

    with pytest.raises(FileReviewNameConflict) as failure:
        save_file_review_object_name(
            run_id="run-001",
            object_id="object-001",
            object_name="Object 4",
            expected_name="Object 4",
        )

    assert failure.value.current_name == "Storage bench"


def test_file_review_blocks_a_saved_run_with_unverified_pages(monkeypatch):
    from types import SimpleNamespace

    from screens import file_review

    errors = []
    monkeypatch.setattr(file_review, "st", SimpleNamespace(
        session_state={"current_run_id": "partial"}, error=errors.append,
    ))
    monkeypatch.setattr(file_review, "apply_file_review_css", lambda: None)
    monkeypatch.setattr(file_review, "_render_file_review_header_only", lambda _controls: None)
    monkeypatch.setattr(file_review, "_back_to_upload_button", lambda: None)
    monkeypatch.setattr(file_review, "_consume_prepared_file_review_navigation", lambda **_kwargs: {
        "run": {"detection_coverage_warning": "Detection could not review page 3"},
    })

    file_review.render_file_review_screen("company")

    assert errors == ["Detection could not verify every page of the PDF. Upload the PDF again"]


def test_successful_name_projection_revokes_only_the_affected_draft_and_ready_handoff(monkeypatch):
    from copy import deepcopy
    from screens import file_review
    old={'object_key':'object-1','name':'Old name'}
    session={'current_run_id':'run-1','current_estimate_id':'estimate-1',
      'objects_estimation_data_cache':{'estimate-1':{'run_id':'run-1','rows':[deepcopy(old)]}},
      'objects_navigation_ready':{'run_id':'run-1','estimate_id':'estimate-1','data':{'rows':[deepcopy(old)]}},
      'objects_set_price_basis':{'estimate-1':'confirmed','other':'other'},
      'proposal_pdf_urls_by_estimate':{'estimate-1':'v1.pdf','other':'other.pdf'}}
    issued=deepcopy(old)
    monkeypatch.setattr(file_review.st,'session_state',session)
    file_review._accept_object_name_projection('run-1','object-1','New name')
    assert session['objects_estimation_data_cache']['estimate-1']['rows'][0]['name']=='New name'
    assert session['objects_navigation_ready']['data']['rows'][0]['name']=='New name'
    assert session['proposal_pdf_urls_by_estimate']['estimate-1'] is None
    assert session['proposal_pdf_urls_by_estimate']['other']=='other.pdf'
    assert issued==old
