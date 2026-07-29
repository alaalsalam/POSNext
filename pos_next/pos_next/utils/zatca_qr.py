"""
ZATCA Phase-1 QR Code Generator
Generates TLV-encoded Base64 QR data for Saudi e-invoices (ZATCA-compliant).

TLV Tags:
  1 = Seller name
  2 = VAT registration number
  3 = Invoice date/time (ISO 8601)
  4 = Invoice total (including VAT)
  5 = VAT total
"""

import base64
import io
import struct


def _tlv_field(tag: int, value: str) -> bytes:
    """Encode a single TLV field."""
    encoded = value.encode("utf-8")
    return struct.pack("BB", tag, len(encoded)) + encoded


def build_zatca_tlv(seller_name: str, vat_number: str, invoice_datetime: str,
                    invoice_total: str, vat_total: str) -> str:
    """
    Build ZATCA Phase-1 QR code TLV string (Base64 encoded).

    Args:
        seller_name: Company / seller name
        vat_number: 15-digit VAT registration number
        invoice_datetime: ISO 8601 datetime e.g. "2025-07-20T14:30:00"
        invoice_total: Total amount including VAT (string with 2 decimal places)
        vat_total: VAT amount only (string with 2 decimal places)

    Returns:
        Base64-encoded TLV string ready for QR encoding
    """
    tlv = (
        _tlv_field(1, seller_name)
        + _tlv_field(2, vat_number)
        + _tlv_field(3, invoice_datetime)
        + _tlv_field(4, invoice_total)
        + _tlv_field(5, vat_total)
    )
    return base64.b64encode(tlv).decode("utf-8")


def generate_zatca_qr_dataurl(seller_name: str, vat_number: str, invoice_datetime: str,
                               invoice_total: str, vat_total: str) -> str:
    """
    Generate a ZATCA Phase-1 QR code as a PNG data URL.

    Returns:
        str: "data:image/png;base64,..." ready to use in <img src="...">
             Returns empty string on error.
    """
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M

        tlv_b64 = build_zatca_tlv(seller_name, vat_number, invoice_datetime,
                                   invoice_total, vat_total)

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(tlv_b64)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        png_b64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{png_b64}"

    except Exception:
        # Silent fallback — print format will skip the QR block
        return ""
