import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

try:
    import google.generativeai as genai
    GEMINI_API_KEY = "AIzaSyBV38tN7w4YxJPQq6ZWqjOSZ1jKxhNuvjY"
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # It's better to instantiate the model dynamically inside the view to avoid API calls on server startup, 
        # but generative model initialization is safe. We use gemini-1.5-flash as the default since it's the standard.
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai_installed = True
    else:
        model = None
        genai_installed = False
except ImportError:
    genai = None
    model = None
    genai_installed = False

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        if not model:
            return JsonResponse({'error': 'مكتبة google-generativeai غير مسطبة على السيرفر، أو الـ API Key مفقود.'}, status=500)
            
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Here we can add system context or tools later
            prompt = f"""
            أنت مساعد ذكي مدمج في نظام ERP (Redivio). 
            مهمتك هي مساعدة المستخدمين على استخدام النظام والإجابة على استفساراتهم باختصار وبطريقة احترافية.
            
            سؤال المستخدم:
            {user_message}
            """
            
            response = model.generate_content(prompt)
            return JsonResponse({'reply': response.text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=400)
