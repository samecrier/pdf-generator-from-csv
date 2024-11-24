import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from collections import defaultdict
from pprint import pprint
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from pdfgenerator.custom_paragraph import CustomParagraph
from math import floor, ceil

pdfmetrics.registerFont(TTFont("Consolas", "data/consola.ttf"))



class GeneratePdf():
	
	HEADER_TOPPADDING = 1
	HEADER_BOTTOMPADDING = 1
	HEADER_LEFTPADDING = 1
	HEADER_RIGHTPADDING = 0
	BRAND_MODEL_TOPPADDING = 1
	BRAND_MODEL_BOTTOMPADDING = 1
	BRAND_MODEL_LEFTPADDING = 1
	BRAND_MODEL_RIGHTPADDING = 0
	APPLICATION_LEFTPADDING = 1
	APPLICATION_RIGHTPADDING = 0
	PARTS_TOPPADDING = 1
	PARTS_BOTTOMPADDING = 1


	def __init__(self, csv_file):
		data = pd.read_csv(csv_file, sep=';', keep_default_na=False, dtype=str)
		data['Y_1'] = pd.to_datetime(data.iloc[:, 2], format="%y.%m", errors='coerce')
		data['Y_2'] = pd.to_datetime(data.iloc[:, 3], format="%y.%m", errors='coerce')
		
		self.headers = [data.columns.tolist()[2:]]
		values = data.values.tolist()


		self.brands_dict = defaultdict(list)
		
		for value in values:
			brand = value[0]
			data = value[1:]
			self.brands_dict[brand].append(data)
		for key in self.brands_dict:
			self.brands_dict[key] = sorted(self.brands_dict[key], key=lambda x: x[0])
		
		
		self.margin_top = 10
		self.margin_bottom = 24
		# a4_variable = A4[1] - не учитывает отступы SimpleDocTemplete
		a4_variable = 829
		self.height = a4_variable - (self.margin_top+self.margin_bottom)

		excel_widths_pixels = [42, 42, 78, 72, 64, 39, 89, 71, 90, 90, 90, 90]
		self.col_widths_points = [w * 0.68 for w in excel_widths_pixels]

		self.elements = []
		self.table_elements = []
		self.span_commands = []
		self.available_height = self.height
		self.current_height = 0

		self.styles = getSampleStyleSheet()
		
		self.styles["Normal"].fontSize = 8
		self.styles["Normal"].leading = 10
		self.initialize_styles()
		# self.style_normal = self.styles["Normal"]
		# self.style_normal.alignment = TA_CENTER

	def initialize_styles(self):
		self.header_style = self.styles["Normal"].clone('Header')
		# self.header_style.fontSize = 8
		# self.header_style.leading = 10
		
		self.brand_model_style = self.styles["Normal"].clone('Brand')
		self.brand_model_style.splitLongWords = False
		# self.brand_model_style.fontSize = 8
		# self.brand_model_style.leading = 10
		self.brand_style = self.styles["Normal"].clone('Brand')
		self.model_style = self.styles["Normal"].clone('Model')
		
		self.main_style = self.styles["Normal"].clone('Main')

		self.years_style = self.styles["Normal"].clone('Years')
		self.application_style = self.styles["Normal"].clone('App')
		self.application_style.alignment = TA_LEFT
		# self.application_style.wordWrap = 'CJK'
		self.application_option_style = self.styles["Normal"].clone('AppOption')
		self.application_option2_style = self.styles["Normal"].clone('AppOption2')
		self.parts_style = self.styles["Normal"].clone('Parts')
		self.parts_style.alignment = TA_CENTER
		
		self.parts_option_style = self.styles["Normal"].clone('PartsOpt')
		self.parts_option2_style = self.styles["Normal"].clone('PartsOpt2')

	
	def get_element_height(self, element):
		width, height = element.wrap(0, 0)
		return height

	def create_doc(self, output_file):
		doc = SimpleDocTemplate(
			output_file,
			pagesize=A4,
			topMargin=self.margin_top,
			bottomMargin=self.margin_bottom)
		return doc

	def get_models(self, data_row, model_name):
		if data_row:
			current_model = []
			for i, cell in enumerate(data_row):
				if cell[0] == model_name:
					current_model.append(data_row[i])
		else:
			current_model = None
		return current_model
	

	def get_height_span_rows(self, max_height_result, span_rows):
		span_rows_height = 0
		span_max = []
		for row_idx in span_rows:
			span_rows_height += max_height_result[row_idx]
			span_max.append(max_height_result[row_idx])
		return span_rows_height, span_max


	def get_span_rows(self, row_idx, col_idx, spans):
		"""
		Определяет индексы строк, которые находятся в одном SPAN с текущей ячейкой.

		Args:
			row_idx (int): Индекс строки текущей ячейки.
			col_idx (int): Индекс столбца текущей ячейки.
			spans (dict): Словарь с SPAN диапазонами, где ключ — начальная ячейка (start_col, start_row),
						а значение — конечная ячейка (end_col, end_row).

		Returns:
			list: Список индексов строк, которые находятся в одном SPAN с текущей ячейкой.
		"""
		for (start_col, start_row), (end_col, end_row) in spans.items():
			if start_row <= row_idx <= end_row and start_col <= col_idx <= end_col:
				# Если ячейка находится в SPAN, возвращаем список строк этого SPAN
				return list(range(start_row, end_row + 1))

		# Если ячейка не входит ни в один SPAN
		return []


	def get_max_heights_no_span(self, table_data, spans):
		"""
		Возвращает словарь, где ключ — индекс строки, а значение — максимальная высота ячейки,
		которая не принадлежит никакому SPAN.

		Args:
			table_data (list of list): Данные таблицы (двумерный массив ячеек).
			spans (dict): Словарь с SPAN диапазонами, где ключ — начальная ячейка (start_col, start_row),
						а значение — конечная ячейка (end_col, end_row).

		Returns:
			dict: Словарь {row_idx: max_height}, где row_idx — индекс строки, а max_height — максимальная
				высота ячейки вне SPAN.
		"""
		result = {}

		for row_idx, row in enumerate(table_data):
			max_height = 0

			for col_idx, cell in enumerate(row):
				# Проверяем, входит ли текущая ячейка в какой-либо SPAN
				is_in_span = any(
					start_row <= row_idx <= end_row and start_col <= col_idx <= end_col
					for (start_col, start_row), (end_col, end_row) in spans.items()
				)

				if not is_in_span:
					# Если ячейка не в SPAN, обновляем max_height
					cell_height = cell.height if hasattr(cell, 'height') else 0
					max_height = max(max_height, cell_height)

			# Сохраняем результат для текущей строки
			result[row_idx] = max_height

		return result


	def get_span_lines(self, row_idx, col_idx, spans):
		"""
		Возвращает количество строк в объединённом SPAN для текущей ячейки.

		Args:
			row_idx (int): Индекс строки текущей ячейки.
			col_idx (int): Индекс столбца текущей ячейки.
			spans (dict): Словарь с SPAN диапазонами, где ключ — начальная ячейка (start_col, start_row),
						а значение — конечная ячейка (end_col, end_row).

		Returns:
			int: Количество строк в SPAN.
		"""
		for (start_col, start_row), (end_col, end_row) in spans.items():
			if start_row <= row_idx <= end_row and start_col <= col_idx <= end_col:
				return end_row - start_row + 1  # Количество строк в SPAN
		return 1  # Если ячейка не входит в SPAN, возвращаем 1

	def calculate_table_height_with_span(self, table, span_commands):
		"""
		Рассчитывает высоту таблицы с учетом вертикального объединения (SPAN) и отступов (PADDINGTOP, PADDINGBOTTOM),
		если все содержимое таблицы обернуто в Paragraph.
		"""
		row_heights = [0] * len(table._cellvalues)  # Для сохранения высот строк
		spans = {}
		colWidths = self.col_widths_points
		# Сбор данных о PADDINGTOP и PADDINGBOTTOM
		for cmd in span_commands:
			if cmd[0] == 'SPAN':
				(start_col, start_row), (end_col, end_row) = cmd[1], cmd[2]
				spans[(start_col, start_row)] = (end_col, end_row)
			# elif cmd[0] == 'TOPPADDING':
			# 	_, (col, row), _, value = cmd
			# 	paddings[(col, row)]['top'] = value
			# elif cmd[0] == 'BOTTOMPADDING':
			# 	_, (col, row), _, value = cmd
			# 	paddings[(col, row)]['bottom'] = value

		max_height_result = self.get_max_heights_no_span(table._cellvalues, spans)
		# print(max_height_result)
		# Рассчет высот строк
		for row_idx, row in enumerate(table._cellvalues):
			for col_idx, cell in enumerate(row):
				if isinstance(cell, CustomParagraph):
					# Получаем высоту через wrap
					height = cell.calculate_custom_height()
					is_span_cell = any(
						start_row <= row_idx <= end_row and start_col <= col_idx <= end_col
						for (start_col, start_row), (end_col, end_row) in spans.items()
					)
					if is_span_cell:
						span_lines = self.get_span_lines(row_idx, col_idx, spans)
						span_rows = self.get_span_rows(row_idx, col_idx, spans)
						span_rows_height, span_max = self.get_height_span_rows(max_height_result, span_rows)
						paddings = cell.bottompadding+cell.toppadding
						# print(col_idx, span_rows_height, height)
						if span_rows_height < height:
							height = cell.height/span_lines+paddings
							row_more_height = [x+paddings for x in span_max if x+paddings > height]
							if row_more_height:
								new_span_max = [x+paddings for x in span_max if x+paddings <= height]
								new_span_lines = len(new_span_max)
								height = (cell.height-sum(row_more_height)+(len(new_span_max)*paddings))/new_span_lines
						elif span_rows_height >= height:
							height = cell.default_height+paddings
					
					row_heights[row_idx] = max(row_heights[row_idx], height)
		
		print(f"sum {sum(row_heights)} {row_heights}")
		total_height = sum(row_heights)
		return total_height, row_heights


	def generate_test_table(self, *args, height_to_increase=0, table_row_heights=None):
		list_for_test_table = []
		for arg in args:
			list_for_test_table.extend(arg)

		value_for_styles = [row[0] for row in list_for_test_table]
		test_data_row = [row[1:] for row in list_for_test_table]
		
		self.span_commands = []

		c_p = [] #8
		c_fb = [] #9
		c_fd = [] #10
		c_rb = [] #11
		c_rd = [] #12

		for i in range(len(value_for_styles)):
			if value_for_styles[i] == 'header':
				self.span_commands.append(('GRID', (0, i), (-1, i), 0.5, colors.black))
				self.span_commands.append(('ALIGN', (0, i), (-1, i), 'CENTER'))
				self.span_commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				self.span_commands.append(('LEFTPADDING', (0, i), (-1, i), 1))
				self.span_commands.append(('RIGHTPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('TOPPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('BOTTOMPADDING', (0, i), (-1, i), 0))
			elif value_for_styles[i] == 'brand':
				self.span_commands.append(('BACKGROUND', (0, i), (-1, i), colors.darkkhaki))
				self.span_commands.append(('GRID', (0, i), (-1, i), 0.5, colors.black))
				self.span_commands.append(('SPAN', (0, i), (-1, i)))
				self.span_commands.append(('ALIGN', (0, i), (-1, i), 'LEFT'))
				self.span_commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				self.span_commands.append(('LEFTPADDING', (0, i), (-1, i), 1))
				self.span_commands.append(('RIGHTPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('TOPPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('BOTTOMPADDING', (0, i), (-1, i), 0))
			elif value_for_styles[i] == 'model':
				self.span_commands.append(('BACKGROUND', (0, i), (-1, i), colors.lightcoral))
				self.span_commands.append(('GRID', (0, i), (-1, i), 0.5, 'black'))
				self.span_commands.append(('SPAN', (0, i), (-1, i)))
				self.span_commands.append(('ALIGN', (0, i), (-1, i), 'LEFT'))
				self.span_commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				self.span_commands.append(('LEFTPADDING', (0, i), (-1, i), 1))
				self.span_commands.append(('RIGHTPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('TOPPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('BOTTOMPADDING', (0, i), (-1, i), 0))
			elif value_for_styles[i] == 'parts':
				self.span_commands.append(('BACKGROUND', (0, i), (-1, i), 'rgb(255, 249, 215)'))
				self.span_commands.append(('GRID', (0, i), (-1, i), 0.5, 'black'))
				self.span_commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				self.span_commands.append(('LEFTPADDING', (0, i), (-1, i), 0))
				self.span_commands.append(('LEFTPADDING', (2, i), (6, i), self.APPLICATION_LEFTPADDING))
				self.span_commands.append(('RIGHTPADDING', (0, i), (-1, i), self.APPLICATION_RIGHTPADDING))
				self.span_commands.append(('TOPPADDING', (0, i), (-1, i), self.PARTS_TOPPADDING))
				self.span_commands.append(('BOTTOMPADDING', (0, i), (-1, i), self.PARTS_BOTTOMPADDING))

		for a, row in enumerate(list_for_test_table):
			for i, cell in enumerate(row):
				if i == 8: #c_p
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_p:
								self.span_commands.append(('SPAN', (i-1, a-len(c_p)), (i-1, a)))
								self.span_commands.append(('GRID', (i-1, a-len(c_p)), (i-1, a), 0.5, 'black'))
								c_p.append(part_text)
							elif c_p == []:
								c_p.append(part_text)
							else:
								c_p = [part_text]
						else:
							c_p = []
					else:
						c_p = []
				if i == 9: #c_fb
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_fb:
								self.span_commands.append(('SPAN', (i-1, a-len(c_fb)), (i-1, a)))
								self.span_commands.append(('GRID', (i-1, a-len(c_fb)), (i-1, a), 0.5, 'black'))
								c_fb.append(part_text)
							elif c_fb == []:
								c_fb.append(part_text)
							else:
								c_fb = [part_text]
						else:
							c_fb = []
					else:
						c_fb = []
				if i == 10: #c_fd
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_fd:
								self.span_commands.append(('SPAN', (i-1, a-len(c_fd)), (i-1, a)))
								self.span_commands.append(('GRID', (i-1, a-len(c_fd)), (i-1, a), 0.5, 'black'))
								c_fd.append(part_text)
							elif c_fd == []:
								c_fd.append(part_text)
							else:
								c_fd = [part_text]
						else:
							c_fd = []
					else:
						c_fd = []
				if i == 11: #c_rb
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_rb:
								self.span_commands.append(('SPAN', (i-1, a-len(c_rb)), (i-1, a)))
								self.span_commands.append(('GRID', (i-1, a-len(c_rb)), (i-1, a), 0.5, 'black'))
								c_rb.append(part_text)
							elif c_rb == []:
								c_rb.append(part_text)
							else:
								c_rb = [part_text]
						else:
							c_rb = []
					else:
						c_rb = []
				if i == 12: #c_rd
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_rd:
								self.span_commands.append(('SPAN', (i-1, a-len(c_rd)), (i-1, a)))
								self.span_commands.append(('GRID', (i-1, a-len(c_rd)), (i-1, a), 0.5, 'black'))
								c_rd.append(part_text)
							elif c_rd == []:
								c_rd.append(part_text)
							else:
								c_rd = [part_text]
						else:
							c_rd = []
					else:
						c_rd = []
		final_table = False
		
		if height_to_increase > 0:
			final_table = True
			final_table_row_heights = table_row_heights[:]
			rows_count = len(table_row_heights)
			loop_counter = 0
			rows_counter = 0

			while height_to_increase > 0.1:
				loop_counter += 1
				
				if loop_counter % 2 == 1:
					if value_for_styles[rows_counter] == 'parts':
						final_table_row_heights[rows_counter] += 1
						height_to_increase -= 1
					if rows_counter + 1 == rows_count:
						rows_counter = 0
					else:
						rows_counter += 1
			print(f"sum {sum(final_table_row_heights)} {final_table_row_heights}")
			# else:
			# 	# print(paddings_dict)
			# 	spans = {}
			# 	for cmd in self.span_commands:
			# 		if cmd[0] == 'SPAN':
			# 			(start_col, start_row), (end_col, end_row) = cmd[1], cmd[2]
			# 			spans[(start_col, start_row)] = (end_col, end_row)
				
			# 	max_height_result = self.get_max_heights_no_span(test_data_row, spans)
			# 	for row_idx, row in enumerate(test_data_row):
			# 		# Проверяем, если текущая строка относится к 'parts'
			# 		if value_for_styles[row_idx] == 'parts':
			# 			# Получаем значения отступов
			# 			toppadding = paddings_dict[row_idx][0]
			# 			bottompadding = paddings_dict[row_idx][1]
			# 			height_max = None
			# 			height_original_max = 0
			# 			# Обновляем отступы в CustomParagraph
			# 			for col_idx, cell in enumerate(row):  # Итерируемся по ячейкам строки
			# 				if isinstance(cell, CustomParagraph):
			# 					# Устанавливаем новые отступы для CustomParagraph
			# 					cell.set_padding(toppadding=toppadding + self.PARTS_TOPPADDING, 
			# 									bottompadding=bottompadding + self.PARTS_BOTTOMPADDING)
			# 									# Добавляем отступы в span_commands
			# 					height = cell.calculate_custom_height()
								
			# 					is_span_cell = any(
			# 						start_row <= row_idx <= end_row and start_col <= col_idx <= end_col
			# 						for (start_col, start_row), (end_col, end_row) in spans.items()
			# 					)
							
			# 					if is_span_cell:
			# 						span_lines = self.get_span_lines(row_idx, col_idx, spans)
			# 						span_rows = self.get_span_rows(row_idx, col_idx, spans)
			# 						span_rows_height = self.get_height_span_rows(max_height_result, span_rows)
			# 						if span_rows_height >= height:
			# 							height = cell.default_height
			# 						elif span_rows_height < height:
			# 							height = cell.height/span_lines
			# 						if height_max == None:
			# 							height_max = height
			# 						else:
			# 							height_max = max(height, height_max)

			# 					else:
			# 						height_original_max = max(cell.height, height_original_max)
			# 			if height_max and height_max > height_original_max:
							
			# 				padding_height = height_max + height_original_max
							
			# 				if padding_height % 2 == 0:
			# 					_toppadding = padding_height/2
			# 					_bottompadding = padding_height/2
			# 				elif padding_height % 2 == 1:
			# 					_toppadding = floor(padding_height / 2)# Округление вниз
			# 					_bottompadding = ceil(padding_height / 2)  # Округление вверх
			# 				print(f"row_idx {row_idx} top {_toppadding} bot {_bottompadding} height max {height_max} orig max {height_original_max}")
			# 				# self.span_commands.append(('TOPPADDING', (0, row_idx), (-1, row_idx), _toppadding+self.PARTS_TOPPADDING))
			# 				# self.span_commands.append(('BOTTOMPADDING', (0, row_idx), (-1, row_idx), _bottompadding+self.PARTS_BOTTOMPADDING))
							
			# 			# else:
			# 			# 	self.span_commands.append(('TOPPADDING', (0, row_idx), (-1, row_idx), toppadding+self.PARTS_TOPPADDING))
			# 			# 	self.span_commands.append(('BOTTOMPADDING', (0, row_idx), (-1, row_idx), bottompadding+self.PARTS_BOTTOMPADDING))
		if final_table:
			test_table = Table(test_data_row, colWidths=self.col_widths_points, rowHeights=final_table_row_heights)		
			# test_table = Table(test_data_row, colWidths=self.col_widths_points)		

		else:
			test_table = Table(test_data_row, colWidths=self.col_widths_points)
		
		if final_table:
			test_table.setStyle(TableStyle(self.span_commands))
			
		else:
			test_table.setStyle(TableStyle(self.span_commands))
		return test_table

	def generate_grouped_model_data(self, model_list):
		data = {
			'Y_1': [cell[1] for cell in model_list],
			'Y_2': [cell[2] for cell in model_list],
			'APP_1': [cell[3] for cell in model_list],
			'APP_2': [cell[4] for cell in model_list],
			'APP_3': [cell[5] for cell in model_list],
			'APP_4': [cell[6] for cell in model_list],
			'APP_5': [cell[7] for cell in model_list],
			'PARKING': [cell[8] for cell in model_list],
			'FR BR': [cell[9] for cell in model_list],
			'FR DS': [cell[10] for cell in model_list],
			'RR BR': [cell[11] for cell in model_list],
			'RR DS': [cell[12] for cell in model_list],
		}
		df = pd.DataFrame(data)

		grouped_df = df.groupby(['PARKING', 'FR BR', 'FR DS', 'RR BR', 'RR DS'], as_index=False).agg({
			'Y_1': 'min',
			'Y_2': 'max',
			'APP_1': lambda x: ', '.join(sorted(set(filter(None, x)))), 
			'APP_2': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'APP_3': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'APP_4': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'APP_5': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'PARKING': 'first',
			'FR BR': 'first',
			'FR DS': 'first',
			'RR BR': 'first',
			'RR DS': 'first'
		})

		sorted_grouped_df = grouped_df.sort_values(by=['Y_1', 'APP_1'], ascending=[True, True])
		sorted_grouped_df['Y_1'] = sorted_grouped_df['Y_1'].dt.strftime('%y.%m')
		sorted_grouped_df['Y_2'] = sorted_grouped_df['Y_2'].dt.strftime('%y.%m')
		model_data= [
			[CustomParagraph(str(cell), 
			self.application_style if i in [2, 3, 4, 5, 6] else self.parts_style, 
			default_width=self.col_widths_points[i],
			leftpadding=self.APPLICATION_LEFTPADDING if i in [2, 3, 4, 5, 6] else 0,
			rightpadding=self.APPLICATION_RIGHTPADDING if i in [2, 3, 4, 5, 6] else 0,
			toppadding=self.PARTS_TOPPADDING,
			bottompadding=self.PARTS_BOTTOMPADDING)
			for i, cell in enumerate(row)] 
			for row in sorted_grouped_df.values
		]
		return model_data

	def generate_models_in_brand(self, brand_data_row):
		models_in_brand = []
		for cell in brand_data_row:
			if cell[0] not in models_in_brand:
				models_in_brand.append(cell[0])
		return models_in_brand
	
	def generate_header_data(self):
		header_data = ['header'] + [CustomParagraph(
			col, 
			self.header_style,
			default_width=self.col_widths_points[i],
			toppadding=self.HEADER_TOPPADDING,
			bottompadding=self.HEADER_BOTTOMPADDING,
			leftpadding=self.HEADER_LEFTPADDING,
			rightpadding=self.HEADER_RIGHTPADDING)
		for i, col in enumerate(self.headers[0])]
		return header_data
	
	def generate_template_list(self):
		list_for_test_table = []
		header_data = self.generate_header_data()
		list_for_test_table.append(header_data)
		return list_for_test_table
	
	def generate_brand_name(self, brand):
		span_width = sum(self.col_widths_points)  # Рассчитываем ширину объединенной ячейки
		
		# Используем Paragraph вместо обычного Paragraph
		brand_name_Paragraph = CustomParagraph(
			brand, 
			self.brand_model_style, 
			default_width=span_width,
			toppadding = self.BRAND_MODEL_TOPPADDING,
			bottompadding = self.BRAND_MODEL_BOTTOMPADDING,
			leftpadding=self.BRAND_MODEL_LEFTPADDING,
			rightpadding=self.BRAND_MODEL_RIGHTPADDING
			)

		# Возвращаем строку
		brand_name = ['brand', brand_name_Paragraph] + [""] * (len(self.headers[0]) - 1)
		
		return brand_name
	
	def generate_model_name_row(self, model_name):
		span_width = sum(self.col_widths_points)  # Рассчитываем ширину объединенной ячейки
		
		# Используем Paragraph вместо обычного Paragraph
		model_name_Paragraph = CustomParagraph(
			model_name, 
			self.brand_model_style, 
			default_width=span_width,
			toppadding = self.BRAND_MODEL_TOPPADDING,
			bottompadding = self.BRAND_MODEL_BOTTOMPADDING,
			leftpadding=self.BRAND_MODEL_LEFTPADDING,
			rightpadding=self.BRAND_MODEL_RIGHTPADDING
		)

		# Возвращаем строку
		model_name_row = ['model', model_name_Paragraph] + [""] * (len(self.headers[0]) - 1)
		return model_name_row
	
	def generate_page(self, page_list, height_to_increase, table_row_heights):
		print(f"to increase {height_to_increase}")
		ended_page = self.generate_test_table(page_list, height_to_increase=height_to_increase, table_row_heights=table_row_heights)
		self.table_elements.append(ended_page)
	
	def move_to_next_page(self):
		print('ПЕРЕХОЖУ В СЛЕД СТРАНИЦУ')
		print('**************************************************************')
		self.table_elements.append(PageBreak())
	
	def generate_pdf_2(self):
		doc = self.create_doc('pdf/new_mock_2.pdf')
		
		
		for brand in self.brands_dict:
			brand_data_row = self.brands_dict[brand]
			models_in_brand = self.generate_models_in_brand(brand_data_row)
			
			input_brand_name = False
			model_data = None
			ended_page = None

			page_list = self.generate_template_list()

			while models_in_brand:
				if input_brand_name == False:
					brand_name = self.generate_brand_name(brand)
					page_list.append(brand_name)
					input_brand_name = True
				if models_in_brand:
					model_name = models_in_brand.pop(0)
				else:
					break
				
				if not model_data:
					current_model = self.get_models(brand_data_row, model_name)
					model_data = self.generate_grouped_model_data(current_model)

				while model_data:
					input_model_name = False
					test_table = self.generate_test_table(page_list)
					test_table_height, table_row_heights = self.calculate_table_height_with_span(test_table, self.span_commands)
					# print('in model data', model_name, self.height, test_table_height)
					while self.height >= test_table_height:
						if not model_data:
							for_final = page_list
							break
						if input_model_name == False:
							model_name_row = self.generate_model_name_row(model_name)
							new_row = ['parts'] + model_data[0] #абсолютно 0 идей почему [new_row] до вызова функции не работает, а во время - работает
							test_table = self.generate_test_table(page_list, [model_name_row], [new_row])
							test_table_height, table_row_heights = self.calculate_table_height_with_span(test_table, self.span_commands)
							# print('in >=', model_name, self.height, test_table_height)
							if self.height >= test_table_height:
								model_data.pop(0)
								page_list.append(model_name_row)
								page_list.append(new_row)
								input_model_name = True
							else:
								test_table = self.generate_test_table(page_list)
								test_table_height, table_row_heights = self.calculate_table_height_with_span(test_table, self.span_commands)
								height_to_increase = self.height - test_table_height
								# print(f"увеличить {height_to_increase} height {self.height} test_table {test_table_height}")
								self.generate_page(page_list, height_to_increase, table_row_heights)
								self.move_to_next_page()
								page_list = self.generate_template_list()
								ended_page = None
								break
						try:
							new_row = ['parts'] + model_data[0] #абсолютно 0 идей почему [new_row] до вызова функции не работает, а во время - работает
						except IndexError:
							break
						
						test_table = self.generate_test_table(page_list, [new_row])
						test_table_height, table_row_heights = self.calculate_table_height_with_span(test_table, self.span_commands)
						# print('check new row', model_name, self.height, test_table_height)
						if self.height >= test_table_height:
							# print(f"if self height after check {model_name}")
							model_data.pop(0)
							page_list.append(new_row)
						else:
							test_table = self.generate_test_table(page_list)
							test_table_height, table_row_heights = self.calculate_table_height_with_span(test_table, self.span_commands)
							height_to_increase = self.height - test_table_height
							# print(f"увеличить {height_to_increase} height {self.height} test_table {test_table_height}")
							self.generate_page(page_list, height_to_increase, table_row_heights)
							self.move_to_next_page()
							page_list = self.generate_template_list()
							ended_page = None
							break
			else:
				if ended_page == None:
					height_to_increase=self.height-test_table_height
					# print(height_to_increase)
					self.generate_page(page_list, height_to_increase=height_to_increase, table_row_heights=table_row_heights)
					self.move_to_next_page()
					page_list = self.generate_template_list()

		doc.build(self.table_elements)

if __name__ == '__main__':
	x = GeneratePdf('data/data.csv')
	x.generate_pdf_2()