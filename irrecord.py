import time
import importlib
import os

class infra_red_record:
	
	ir_sensor_th = 36
	lib = "/usr/lib/python3.5/ircgpiolite/"
	
	def __init__(self, gpio_module, ir_name, pin):
		self.gpio_module = gpio_module
		self.pin = pin
		self.ir_name = ir_name
		
	def __make_codes_pyfile(self, filename, dict, _len, buttons):
		f = open(filename,"w")
		f.write("code_len = ")
		f.write(str(_len))
		f.write("\n")
		f.write("btn_codes = {\n")
		i = 0
		for b in buttons:
			f.write("\'")
			f.write(b)
			f.write("\' ")
			f.write(": [")
			j = 0
			for c in dict.get(b):
				f.write(str(c))
				if(j != len(dict.get(b)) - 1):
					f.write(", ")
				else:
					f.write("]")
				j = j + 1
			if(i != len(buttons) - 1):
				f.write(",\n")
			else:
				f.write("\n}")
			i = i + 1
		
		f.close()
		
	def __count(self, lst):
		map = []
		for l in lst:
			fq = 0
			for r in lst:
				if l == r:
					fq = fq + 1
			map.append([l,fq])
		
		res = []
	
		for i in range (0,len(map)):
			if i == 0:
				res.append(map[i])
			else:
				if map[i] not in res:
					res.append(map[i])
	
		return res
	
	def __find_calibr_param(self, lst, th):
		max = [[0,0]]
		for l in lst:
			if l[1] > max[0][1]:
				max[0] = l
			
		if max[0][1] < th:
			return -1
		
		if max[0][1] >= th:	
			return max[0][0]
	
	def __calibration(self):
	
		GPIO = importlib.import_module(self.gpio_module)
				
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin, GPIO.IN)
		
		buffer = []
		calibr = []
		print("Startting calibration")
		ic = 0
		while True:
			tic = time.time()
			GPIO.wait_for_edge(self.pin, GPIO.FALLING)
			toc = time.time()
			if (toc - tic < 1):
				if ((toc - tic)*1000 < self.ir_sensor_th):
					buffer.append(float("{0:.3f}".format((toc - tic)*1000)))
				else:
					print("Calibration step ", ic)
					calibr.append(len(buffer.copy()))
					buffer.clear()
					ic = ic + 1
					if ic == 11:
						ic = 0
						cparams = self.__count(calibr.copy())
						print(cparams)
						calibr.clear()
						print("Start calibration again? (Y/any key)")
						inp = input()
						if inp == "Y":
							print("New calibration")
						else:
							cp = self.__find_calibr_param(cparams, 5)
							if (cp == -1):
								print("Calibration parameter has hot been defined, starting calibration again")
							else:
								return cp

	def __get_max(self, lst):
		max = 0
		for l in lst:
			if l > max:
				max = l
	
		return max
	
	def __dispersion(self, lst):
		max = self.__get_max(lst)
		_disp = []
	
		for l in lst:
			if l >= 0.8 * max:
				_disp.append(2 * (max - l))
			
		disp = 0
		sum = 0
		for d in _disp:
			sum = sum + d
	
		disp = sum / len(_disp)
		_disp.clear()
	
		return disp

	def __dcalibration(self, p_calib):
	
		GPIO = importlib.import_module(self.gpio_module)
				
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin, GPIO.IN)
		
		buffer = []
		avg = []
		ic2 = 0
		print("Startting double calibration")
		while True:
			tic = time.time()
			GPIO.wait_for_edge(self.pin, GPIO.FALLING)
			toc = time.time()
			if (toc - tic < 1):
				if ((toc - tic)*1000 < self.ir_sensor_th):
					buffer.append(float("{0:.3f}".format((toc - tic)*1000)))
				else:
					if (len(buffer) == p_calib):
						print("Double calibration step ", ic2)
						print (buffer)
						avg.append(buffer.copy()[0])
						ic2 = ic2 + 1
						if ic2 == 11:
							max = self.__get_max(avg)
							disp = float("{0:.3f}".format(self.__dispersion(avg)))
							avg.clear()
							res = [max, disp]
							return res
						
					buffer.clear()

	def __frecord(self, p_calib, irsteps, corr = [0,0]):
	
		GPIO = importlib.import_module(self.gpio_module)
				
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin, GPIO.IN)
		
		buffer = []
		record = []
		if len(record) != 0:
			record.clear()
		print("Recording...")
		ir = 1
		while True:
			tic = time.time()
			GPIO.wait_for_edge(self.pin, GPIO.FALLING)
			toc = time.time()
			if (toc - tic < 1):
				if ((toc - tic)*1000 < self.ir_sensor_th):
					buffer.append(float("{0:.3f}".format((toc - tic)*1000)))
				else:
					max = self.__get_max(buffer)
					if (len(buffer) == p_calib):
						if corr != [0,0]:
							print(corr)
							if max < corr[0] - corr[1]:
								continue
						print("Record step ", ir)
						print (buffer)
						record.append(buffer.copy())
						ir = ir + 1
						if ir == irsteps + 1:
							ir = 1
							tmp = []
							for i in range(0,p_calib):
								sum = 0
								for j in range (0, irsteps):
									sum = record[j][i] + sum
								tmp.append(float("{0:.3f}".format((sum)/irsteps)))
							print("Average")
							print(tmp)
							print("Save record? (Y/any key)")
							inp = input()
							if inp != "Y":
								print("New record")
								tmp.clear()
								record.clear()
							else:
								return tmp.copy()
					buffer.clear()

	def __save_button(self, p_calib, buttons, corr = [0,0]):
		dict = {}
		for b in buttons:
			print("Record started for button ", b)
			code = self.__frecord(p_calib, 3, corr)
			dict[b] = code
			print("Saved!")

		return dict

	def record(self, buttons):
		p_calib = self.__calibration()
		print("Calibration parameter = ", p_calib)
		amendment = self.__dcalibration(p_calib)
		print("Amendmebt parameter = ", amendment)
		_dict = self.__save_button(p_calib, buttons, amendment)
		path = self.lib + self.ir_name
		if not os.path.exists(path):
			os.makedirs(path)
		path = path + "/code.py"
		self.__make_codes_pyfile(path, _dict, p_calib, buttons)