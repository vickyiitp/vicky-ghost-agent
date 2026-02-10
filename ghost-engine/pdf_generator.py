from fpdf import FPDF
import datetime
import os

class GhostReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'VICKY-GHOST: INTELLIGENCE REPORT', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Generated on {datetime.datetime.now()} | Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(data_list, screenshot_path, output_name="report.pdf"):
    pdf = GhostReport()
    pdf.add_page()
    
    # 1. ADD SCREENSHOT (The Visual Evidence)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, "Captured Source Evidence:", ln=True)
    if os.path.exists(screenshot_path):
        try:
             # Scales image to page width (A4 width is approx 210mm)
             # x=10, w=190 leaves 10mm margins
            pdf.image(screenshot_path, x=10, w=190)
        except Exception as e:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, f"Error embedding image: {str(e)}", ln=True)
            pdf.set_text_color(0, 0, 0)
    else:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "IMAGE EVIDENCE DESTROYED OR MISSING", ln=True)
        pdf.set_text_color(0, 0, 0)
        
    pdf.add_page()

    # 2. ADD DATA TABLE (The Arranged Intelligence)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, "Structured AI Extraction:", ln=True)
    pdf.ln(5)
    
    # Ensure data_list is a list (handle empty or error states)
    if not isinstance(data_list, list):
        pdf.set_font('Helvetica', 'I', 12)
        pdf.cell(0, 10, "No structured data to display.", ln=True)
        pdf.output(output_name)
        return

    # Table Header logic
    if data_list:
        # Get all unique keys from all dictionaries to form columns
        # For simplicity, we'll just take keys from the first item or user 'Key' 'Value' if flattened
        # But generally AI returns varied objects.
        # Let's try to print them as key-value pairs for each item.
        
        pdf.set_font('Helvetica', '', 10)
        
        for i, entry in enumerate(data_list):
            pdf.set_fill_color(30, 30, 30) # Dark Header
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, f"Result #{i+1}", border=1, fill=True, ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(240, 240, 240)
            
            for key, value in entry.items():
                # Key
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(50, 8, str(key), border=1, fill=True)
                
                # Value (handling multiline)
                pdf.set_font('Helvetica', '', 10)
                # multi_cell is tricky in a table row. 
                # Better to use cell for single line or just dump it.
                # Let's clean the string
                val_str = str(value).replace("\n", " ")
                # Truncate if too long?
                if len(val_str) > 75: 
                    val_str = val_str[:72] + "..."
                    
                pdf.cell(0, 8, val_str, border=1, ln=True)
            
            pdf.ln(2)

    pdf.output(output_name)
    return output_name
