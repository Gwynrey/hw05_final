import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    year_today = int(dt.datetime.now().strftime('%Y'))
    return {
        'year': year_today
    }
