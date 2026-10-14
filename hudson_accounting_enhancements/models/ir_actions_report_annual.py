import io
import re
import PyPDF2
from PyPDF2.generic import NameObject, ArrayObject, NumberObject
from odoo import models


class IrActionsReportAnnual(models.Model):
    """Override to ensure internal PDF Table of Contents links work seamlessly
    and do not redirect to external website URLs.
    """

    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        pdf_content, report_type = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        
        report = self._get_report(report_ref)
        if not report or report.report_name != 'hudson_accounting_enhancements.report_annual':
            return pdf_content, report_type

        # Post-process PDF to convert all TOC links to internal PDF page destinations
        try:
            pdf_content = self._fix_annual_report_toc_links(pdf_content)
        except Exception as e:
            # Fallback gracefully if PDF parsing encounters an unexpected structure
            pass

        return pdf_content, report_type

    def _fix_annual_report_toc_links(self, pdf_bytes):
        """Rewrites link annotations in the PDF so TOC links jump directly
        to internal PDF pages instead of resolving as web URLs.
        """
        page_mapping = {
            'attestation': 3,
            'balance_sheet': 4,
            'profit_loss': 5,
            'preamble': 6,
            'accounting_principles': 7,
            'intangible_tangible': 8,
            'inventory_valuation': 9,
            'financial_resources': 10,
            'workforce': 11,
            'aged_payable': 12,
            'aged_receivable': 13,
            'asset_information': 14,
            'liabilities_information': 15,
            'income_statement': 16,
            'taxation': 17,
            'supporting_documents': 18,
        }

        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        writer = PyPDF2.PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        num_pages = len(writer.pages)

        for page_idx, page in enumerate(writer.pages):
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    obj = annot.get_object()
                    dest_str = str(obj.get("/Dest") or "")
                    action_obj = obj.get("/A")
                    uri_str = ""
                    if action_obj:
                        uri_str = str(action_obj.get("/URI") or "")

                    link_target = (dest_str + " " + uri_str).lower()
                    for anchor, target_page_num in page_mapping.items():
                        if anchor in link_target and target_page_num <= num_pages:
                            target_page = writer.pages[target_page_num - 1]
                            dest_array = ArrayObject([
                                target_page.indirect_reference,
                                NameObject("/XYZ"),
                                NumberObject(0),
                                NumberObject(800),
                                NumberObject(0)
                            ])
                            obj[NameObject("/Dest")] = dest_array
                            if NameObject("/A") in obj:
                                del obj[NameObject("/A")]
                            break

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
