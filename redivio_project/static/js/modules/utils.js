export const utils = {
    state: {
        isArabic: true,
        currentTime: '--:--',
        currentDate: 'Loading...',
        showReadyMessage: false,
    },
    methods: {
        startClock(instance) {
            setInterval(() => {
                const now = new Date();
                instance.currentTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                instance.currentDate = now.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
            }, 1000);
        },
        triggerReadySystem(instance) {
            instance.showReadyMessage = true;
            setTimeout(() => { instance.showReadyMessage = false; }, 4000);
        },
        formatDate(dateStr) {
            if(!dateStr) return '---';
            const date = new Date(dateStr);
            return date.toLocaleDateString('ar-EG', { 
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit' 
            });
        },
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    }
};