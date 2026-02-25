import datetime

class TimeTrackerState:
    
    def __init__(self):
        self.sheet = None
        self.current_client = None
        self.is_clocked_in = False
        self.current_row = None
        self.active_start = None
        self.total_active = 0
        self.last_activity = None
        self.current_activity = "Active"
    
    def clock_in(self, row_index, start_time):
        self.is_clocked_in = True
        self.current_row = row_index
        self.active_start = start_time
        self.total_active = 0
        self.last_activity = start_time
        self.current_activity = "Active"
    
    def clock_out(self, end_time):
        if self.active_start:
            self.total_active += (end_time - self.active_start).seconds
        self.is_clocked_in = False
        
    def get_total_seconds(self, current_time):
        elapsed = self.total_active
        if self.is_clocked_in and self.current_activity == "Active" and self.active_start:
            elapsed += (current_time - self.active_start).seconds
        return elapsed