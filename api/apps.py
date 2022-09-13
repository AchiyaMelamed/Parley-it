import sys

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """every time the server is start running,
            rerun scheduled transactions that didn't complete from the point they stopped.
        """
        if "runserver" not in sys.argv:
            return True
        
        from .models import ScheduledTransaction
        from .utils import get_twelve_dates
        from .threads import PerformTransactionEveryWeek
        
        undone_scheduled_transactions = ScheduledTransaction.objects.filter(dates_done__lt=12)
        if undone_scheduled_transactions:
            print(f"found {len(undone_scheduled_transactions)} undone threads...")
            for undone_scheduled_transaction in undone_scheduled_transactions:
                scheduled_dates = get_twelve_dates()
                
                if undone_scheduled_transaction.dates_done == 11:
                    scheduled_dates = scheduled_dates[:1]
                else:
                    scheduled_dates = scheduled_dates[:12 - undone_scheduled_transaction.dates_done]
                advance_transacrion_thread = PerformTransactionEveryWeek(scheduled_transaction=undone_scheduled_transaction,
                                                             scheduled_dates=scheduled_dates)
                advance_transacrion_thread.start()