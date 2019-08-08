
import platform
if platform.system() != 'Windows':
	raise Exception('This will ONLY work on Windows systems!')

from pypykatz.registry.live_reader.reader import LiveRegistryHive
from pypykatz.registry import logger
from pypykatz.registry.sam.sam import *
from pypykatz.registry.security.security import *
from pypykatz.registry.system.system import *

from pypykatz.commons.winapi.processmanipulator import ProcessManipulator


class LiveRegistry:
	def __init__(self):
		self.sam_hive = None
		self.security_hive = None
		self.system_hive = None
		
		self.system = None
		self.sam = None
		self.security = None
		
	def get_secrets(self):
		"""
		For obtaining all secrets from the registry on-the-fly, SYSTEM user MUST be used!
		In case this is not achievable, Administrator can be used to first dump the registry hives to disk, then parse them offline
		There is a 3rd way: As administrator you can obtain SE_TAKE_OWNERSHIP privileges, then you can open any hive with the WRITE_OWNER permission. 
			After doing that you'd need to change the SID of each target hive to include the administrator user with full access.
			This is so intrusive I'm not implementing that, if you mess that up your computer will turn to potato. Like literally... (also it's a lot of work)
		"""
		pm = ProcessManipulator()
		try:
			#getting a SYSTEM token...
			pm.assign_token_thread_sid()
		except Exception as e:
			logging.error('Failed to obtain SYSTEM prvis. On-the-fly parsing is not possible.')
			raise e
		else:
			self.system = SYSTEM(self.system_hive)
			bootkey = self.system.get_bootkey()
			
			if self.sam_hive:
				self.sam = SAM(self.sam_hive, bootkey)
				self.sam.get_secrets()
				
			if self.security_hive:
				self.security = SECURITY(self.security_hive, bootkey)
				self.security.get_secrets()
				
			self.cleanup()
			
	def cleanup(self):
		for hive in [self.system_hive, self.security_hive, self.sam_hive]:
			try:
				hive.close()
			except:
				pass
		
	def to_file(self, json_format = False):
		pass
		
	def __str__(self):
		t = str(self.system)
		if self.sam:
			t += str(self.sam)
		if self.security:
			t += str(self.security)
		return t
		
	@staticmethod
	def go_live():
		lr = LiveRegistry()
		lr.sam_hive = LiveRegistryHive('SAM')
		lr.system_hive = LiveRegistryHive('SYSTEM')
		lr.security_hive = LiveRegistryHive('SECURITY')
		
		lr.get_secrets()
		return lr
