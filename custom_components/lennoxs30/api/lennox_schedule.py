from .lennox_period import lennox_period

class lennox_schedule(object):
    def __init__(self, id):
        self.id = id
        self.name = '<Unknown>'
        self.periodCount = -1
        self._periods = []

    def getOrCreatePeriod(self, id):
        item = self.getPeriod(id)
        if item != None:
            return item
        item = lennox_period(id)
        self._periods.append(item)
        return item

    def getPeriod(self, id):
        for item in self._periods:
            if item.id == id:
                return item
        return None

    def update(self, tschedule):
        if 'schedule' not in tschedule:
            return
        schedule = tschedule['schedule']
        if 'name' in schedule:
            self.name = schedule['name']
        if 'periodCount' in schedule:
            self.periodCount = schedule['periodCount']
        if 'periods' in schedule:
            for periods in schedule['periods']:
                periodId = periods['id']
                lperiod = self.getOrCreatePeriod(periodId)
                lperiod.update(periods)