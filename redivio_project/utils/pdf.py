import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template

def render_to_pdf(template_src, context_dict={}):
    """
    وتحويله إلى ملف PDF أصلي واحترافي HTML تأخذ قالب 
    xhtml2pdf باستخدام مكتبة 
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        # إذا لم يتم تثبيت المكتبة بعد، سيظهر هذا الخطأ المنظم بدلاً من تحطيم النظام
        return HttpResponse(
            "<h1>We need a PDF Library!</h1>"
            "<p>Please ensure you run: <code>pip install xhtml2pdf</code> on your server.</p>", 
            status=501
        )
        
    template = get_template(template_src)
    html = template.render(context_dict)
    
    result = BytesIO()
    # تحويل النص المدخل إلى PDF مع دعم الترميز
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    
    return HttpResponse(f"Error Generating PDF: <pre>{html}</pre>")
