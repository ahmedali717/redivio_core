import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

def get_gemini_api_key():
    return os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")

@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    api_key = get_gemini_api_key()
    if not api_key:
        return JsonResponse({
            'reply': 'المساعد الذكي غير مفعل حالياً. يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات السيرفر.'
        })

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        data = json.loads(request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body)
        user_message = data.get('message', '').strip()
        if not user_message:
            return JsonResponse({'reply': 'مرحباً بك! كيف يمكنني مساعدتك اليوم في نظام Redivio ERP؟'})
            
        model_name = 'gemini-1.5-flash'
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name or 'pro' in m.name:
                        model_name = m.name
                        break
        except Exception:
            pass
            
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        أنت مساعد ذكي مدمج في نظام ERP (Redivio). 
        مهمتك هي مساعدة المستخدمين على استخدام النظام والإجابة على استفساراتهم باختصار وبطريقة احترافية.
        
        سؤال المستخدم:
        {user_message}
        """
        response = model.generate_content(prompt)
        return JsonResponse({'reply': response.text})
    except ImportError:
        return JsonResponse({
            'reply': 'مكتبة الذكاء الاصطناعي google-generativeai غير مثبتة على السيرفر.'
        })
    except Exception as e:
        err_str = str(e)
        if "leaked" in err_str.lower() or "403" in err_str:
            return JsonResponse({
                'reply': 'مفتاح الـ API الحالي غير صالح أو تم إيقافه. يرجى تجديد GEMINI_API_KEY في متغيرات البيئة بالسيرفر.'
            })
        return JsonResponse({'error': f"عذراً، حدث خطأ أثناء معالجة الطلب: {err_str[:150]}"}, status=500)
