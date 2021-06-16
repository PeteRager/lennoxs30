class lennox_period(object):
    def __init__(self, id):
        self.id = id
        self.enabled = False
        self.startTime = None
        self.systemMode = None
        self.hsp = None
        self.hspC = None
        self.csp = None
        self.cspC = None
        self.sp = None
        self.spC = None
        self.humidityMode = None
        self.husp = None
        self.desp = None
        self.fanMode = None

    def update(self, periods):
        if 'enabled' in periods:
            self.enabled = periods['enabled']
        if 'period' in periods:
            period = periods['period']
            if 'startTime' in period:
                self.startTime = period['startTime']
            if 'systemMode' in period:
                self.systemMode = period['systemMode']
            if 'hsp' in period:
                self.hsp = period['hsp']
            if 'hspC' in period:
                self.hspC = period['hspC']
            if 'csp' in period:
                self.csp = period['csp']
            if 'cspC' in period:
                self.cspC = period['cspC']
            if 'sp' in period:
                self.sp = period['sp']
            if 'spC' in period:
                self.spC = period['spC']
            if 'humidityMode' in period:
                self.humidityMode = period['humidityMode']
            if 'husp' in period:
                self.husp = period['husp']
            if 'desp' in period:
                self.desp = period['desp']
            if 'fanMode' in period:
                self.fanMode = period['fanMode']