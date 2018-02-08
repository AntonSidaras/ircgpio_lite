import time
import importlib
import importlib.util

class infra_red_control:
	
	ir_sensor_th = 36
	
	def __init__(self, gpio_module, ir_name, pin):
		self.gpio_module = gpio_module
		self.pin = pin
		self.ir_name = ir_name
		
	def __check_module(self, module_name):
		module_spec = importlib.util.find_spec(module_name)
	
		if module_spec is None:
			return None
		else:
			return module_spec
				
	def __ret_code(self):
	
		module_name = 'ircgpiolite.' + self.ir_name + '.code'
		spec = self.__check_module(module_name)
		if spec != None:
			return importlib.import_module(module_name)
		else:
			return None
				
	def get(self):
	
		code = self.__ret_code()
	
		if code == None:
			return ["",[0]] 
				
		GPIO = importlib.import_module(self.gpio_module)
				
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin, GPIO.IN)
		
		buffer = []
		sqr = []
		buttons = list(code.btn_codes.keys())
		while True:
			tic = time.time()
			GPIO.wait_for_edge(self.pin, GPIO.FALLING)
			toc = time.time()
			if (toc - tic < 1):
				if ((toc - tic)*1000 < self.ir_sensor_th):
					buffer.append(float("{0:.3f}".format((toc - tic)*1000)))
				else:
					if (len(buffer) == code.code_len):
						i = 0
						for b in buttons:
							for digit in range(0,code.code_len):
								sqr.append(float("{0:.3f}".format((code.btn_codes.get(b)[digit] - buffer[digit])**2)))
							same = True
							for d in sqr:
								if d > 1:
									same = False
							if same == True:
								sqr.clear()
								buffer.clear()
								#print(b)
								return [b,code.btn_codes.get(b)]
								GPIO.cleanup()
								#continue
							i = i + 1
							sqr.clear()
					buffer.clear()
		
		GPIO.cleanup()		
		return ["",[0]]