from datetime import datetime
import pytz


def year(request):
    """Добавляет переменную с текущим годом."""
    tz = pytz.timezone('Europe/Moscow')
    dt = datetime.now(tz)
    year = dt.year
    return {
        'year': year
    }
