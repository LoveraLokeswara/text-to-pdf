from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from pydantic import BaseModel

# Create a Pydantic model for the request body
class TextRequest(BaseModel):
    text: str

# Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Text to PDF conversion function
def text_to_pdf(text, max_width=170*mm):
    buffer = BytesIO()                      # Create a buffer to hold the PDF
    c = canvas.Canvas(buffer, pagesize=A4)  # Create a canvas for the PDF
    width, height = A4                      # Get the dimensions of the A4 page
    x_margin, y_margin = 20*mm, 20*mm       # Set margins
    y = height - y_margin                   # Start drawing from the top
    c.setFont("Helvetica", 11)              # Set the font for the PDF

    # Function to wrap lines of text to fit within the specified width
    def wrap_line(line, font_name="Helvetica", font_size=11):
        words = line.split()  # Split the line into words
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()  # Test the current line with the new word
            if stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line  # If it fits, add the word to the current line
            else:
                lines.append(current_line)  # If it doesn't fit, save the current line
                current_line = word  # Start a new line with the current word
        if current_line:
            lines.append(current_line)  # Add the last line if it exists
        return lines

    # Iterate through each line of the text
    for raw_line in text.split("\n"):
        wrapped_lines = wrap_line(raw_line)  # Wrap the line to fit the page
        for line in wrapped_lines:
            if y < y_margin:                    # Check if we need to start a new page
                c.showPage()                    # Create a new page
                c.setFont("Helvetica", 11)      # Reset the font
                y = height - y_margin           # Reset the y position
            c.drawString(x_margin, y, line)     # Draw the line on the PDF
            y -= 14                             # Move down for the next line

    c.save()        # Save the PDF to the buffer
    buffer.seek(0)  # Move to the beginning of the buffer
    return buffer   # Return the buffer containing the PDF

@app.post("/convert")
async def convert_text_to_pdf(request: TextRequest):
    """
    Endpoint to convert text to PDF
    
    Accepts JSON data with a 'text' field
    Returns a PDF file for download
    """
    try:
        # Check if text is empty
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Convert text to PDF
        pdf_buffer = text_to_pdf(request.text)
        
        # Return the PDF as a downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=converted.pdf"
            }
        )
    
    except Exception as e:
        print(f"Error in convert endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
