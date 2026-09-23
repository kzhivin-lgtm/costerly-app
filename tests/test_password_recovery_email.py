from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]


def test_password_recovery_email_uses_public_brand_asset_and_direct_auth_link():
    template = (
        ROOT / "notes/email_templates/password_recovery.html"
    ).read_text(encoding="utf-8")

    assert "https://app.costerly.ai/assets/email/costerly-ai-logo.png" in template
    assert 'alt="Costerly AI"' in template
    assert "{{ .ConfirmationURL }}" in template
    assert "<svg" not in template
    assert "data:image" not in template
    assert "We received your request. Click the button below to create a new password" in template
    assert "Create a new password for your Costerly AI account." not in template
    assert "If you didn’t request this, you can safely ignore this email." not in template
    assert ">Reset your password</a>" in template


def test_password_recovery_subject_is_unique_without_exposing_the_otp():
    subject = (
        ROOT / "notes/email_templates/password_recovery.subject.txt"
    ).read_text(encoding="utf-8").strip()

    assert subject == (
        'Reset your Costerly AI password · {{ printf "%.8s" .TokenHash }}'
    )
    assert "{{ .Token }}" not in subject


def test_password_recovery_email_logo_is_high_density_transparent_png():
    logo_path = ROOT / "cloudflare/assets/email/costerly-ai-logo.png"

    with Image.open(logo_path) as logo:
        assert logo.size == (806, 154)
        assert logo.mode == "RGBA"
