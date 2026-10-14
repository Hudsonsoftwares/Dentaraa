# -*- coding: utf-8 -*-
import json
import io
from odoo import http
from odoo.http import request

class DynamicReportController(http.Controller):
    
    @http.route(['/hudson_dynamic_reports/export_xlsx', '/hudson_accounting_enhancements/export_xlsx'], type='http', auth='user', methods=['POST'], csrf=False)
    def export_xlsx(self, **post):
        try:
            report_data_str = post.get('data', '{}')
            report_data = json.loads(report_data_str)
        except Exception:
            report_data = {}
            
        title = report_data.get('title', 'Report')
        columns = report_data.get('columns', [])
        lines = report_data.get('lines', [])
        date_str = report_data.get('date_str', '')
        
        output = io.BytesIO()
        try:
            import xlsxwriter
        except ImportError:
            return request.make_response("xlsxwriter library is not installed.", headers=[('Content-Type', 'text/plain')])
            
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(title[:31]) # Excel sheet name limit is 31 chars
        
        # Define formats
        format_title = workbook.add_format({'font_size': 14, 'bold': True})
        format_date = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'right'})
        
        format_header = workbook.add_format({
            'bold': True,
            'bottom': 2, # Thick bottom border
            'align': 'right'
        })
        format_header_left = workbook.add_format({
            'bold': True,
            'bottom': 2,
            'align': 'left'
        })
        
        # Row format for top level headers
        format_level1 = workbook.add_format({
            'bold': True,
            'bottom': 6, # Double bottom border
            'top': 1,
            'valign': 'vcenter'
        })
        format_level1_monetary = workbook.add_format({
            'bold': True,
            'bottom': 6,
            'top': 1,
            'valign': 'vcenter',
            'num_format': '#,##0.00'
        })
        
        # Row format for standard levels
        format_standard = workbook.add_format({'valign': 'vcenter'})
        format_standard_monetary = workbook.add_format({
            'valign': 'vcenter',
            'num_format': '#,##0.00'
        })
        
        # Set column widths
        worksheet.set_column(0, 0, 40)
        for i in range(1, len(columns)):
            worksheet.set_column(i, i, 18)
            
        row = 0
        
        # Write Title row
        worksheet.write_string(row, 0, "", format_title) # Empty for exact match
        if date_str:
            worksheet.write_string(row, len(columns) - 1, f"As of {date_str}", format_date)
        row += 1
        
        # Write Header row
        col_idx = 0
        for col in columns:
            fmt = format_header if col.get('type') == 'monetary' else format_header_left
            worksheet.write_string(row, col_idx, col.get('label', ''), fmt)
            col_idx += 1
        row += 1
        
        # Write Lines
        for line in lines:
            try:
                level = int(line.get('level', 1))
            except (ValueError, TypeError):
                level = 1
                
            is_header = level == 1
            
            # Format Name Cell
            name_fmt = workbook.add_format()
            if is_header:
                name_fmt.set_bold()
                name_fmt.set_bottom(6)
                name_fmt.set_top(1)
            else:
                name_fmt.set_color('#555555')
                
            # Set indentation for the name
            if level > 1:
                name_fmt.set_indent(level - 1)
                
            col_idx = 0
            for col in columns:
                field = col.get('field')
                val = line.get(field, '')
                is_monetary = col.get('type') == 'monetary'
                
                # Determine cell format
                if col_idx == 0:
                    cell_fmt = name_fmt
                else:
                    if is_header:
                        cell_fmt = format_level1_monetary if is_monetary else format_level1
                    else:
                        cell_fmt = format_standard_monetary if is_monetary else format_standard
                        
                # Write value
                if is_monetary:
                    try:
                        num_val = float(val) if val not in ('', None) else 0.0
                        if val in ('', None) and is_header:
                            worksheet.write_blank(row, col_idx, '', cell_fmt)
                        else:
                            worksheet.write_number(row, col_idx, num_val, cell_fmt)
                    except ValueError:
                        worksheet.write_string(row, col_idx, str(val), cell_fmt)
                else:
                    text_val = str(val) if val not in ('', None) else ''
                    if is_header and col_idx == 0:
                        text_val = text_val.upper() # Uppercase top level headers
                    worksheet.write_string(row, col_idx, text_val, cell_fmt)
                    
                col_idx += 1
            row += 1
            
        workbook.close()
        output.seek(0)
        
        file_name = f"{title.replace(' ', '_')}.xlsx"
        
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{file_name}"')
            ]
        )
