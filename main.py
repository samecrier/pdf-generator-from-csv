import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from collections import defaultdict
from pprint import pprint

class GeneratePdf():
	
	PADDING_ZERO = [
		('LEFTPADDING', (0, 0), (-1, -1), 0),
		('RIGHTPADDING', (0, 0), (-1, -1), 0),
		('TOPPADDING', (0, 0), (-1, -1), 0),
		('BOTTOMPADDING', (0, 0), (-1, -1), 2),
	]
	PADDING_HEADERS = [
		('LEFTPADDING', (0, 0), (-1, -1), 0),
		('RIGHTPADDING', (0, 0), (-1, -1), 0),
		('TOPPADDING', (0, 0), (-1, -1), 3),
		('BOTTOMPADDING', (0, 0), (-1, -1), 4),
	]
	PADDING_BRAND_MODEL = [
		('LEFTPADDING', (0, 0), (-1, -1), 0),
		('RIGHTPADDING', (0, 0), (-1, -1), 0),
		('TOPPADDING', (0, 0), (-1, -1), -1),
		('BOTTOMPADDING', (0, 0), (-1, 0), 4),
		('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
	]

	PADDING_PARTS = [
		('LEFTPADDING', (0, 0), (-1, -1), 0),
		('RIGHTPADDING', (0, 0), (-1, -1), 0),
		('TOPPADDING', (0, 0), (-1, -1), 0),
		('BOTTOMPADDING', (0, 0), (-1, 0), 2),
		('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
	]



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
		self.margin_bottom = 20
		# a4_variable = A4[1] - не учитывает отступы SimpleDocTemplete
		a4_variable = 829
		self.height = a4_variable - (self.margin_top+self.margin_bottom)

		excel_widths_pixels = [42, 42, 78, 72, 64, 39, 89, 71, 90, 90, 90, 90]
		self.col_widths_points = [w * 0.68 for w in excel_widths_pixels]

		self.elements = []
		self.table_elements = []
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
		self.brand_model_style.fontSize = 8
		self.brand_model_style.leading = 10
		self.brand_style = self.styles["Normal"].clone('Brand')
		self.model_style = self.styles["Normal"].clone('Model')
		
		self.main_style = self.styles["Normal"].clone('Main')

		self.years_style = self.styles["Normal"].clone('Years')
		self.application_style = self.styles["Normal"].clone('App')
		self.application_style.alignment = TA_LEFT
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
	def calculate_table_height_with_span(self, table):
		"""
		Рассчитывает высоту таблицы с учетом вертикального объединения (SPAN).
		"""
		colWidths = self.col_widths_points
		total_height = 0
		row_heights = [0] * len(table._cellvalues)  # Для сохранения высот строк

		for row_idx, row in enumerate(table._cellvalues):
			for col_idx, cell in enumerate(row):
				if isinstance(cell, Paragraph):
					_, height = cell.wrap(colWidths[col_idx], 0)
					row_heights[row_idx] = max(row_heights[row_idx], height)
				elif isinstance(cell, str):
					# Задаем стандартную высоту для строк с текстом
					row_heights[row_idx] = max(row_heights[row_idx], 12)

		# Обрабатываем SPAN
		for cmd in table._tblStyle.commands:
			if cmd[0] == 'SPAN':
				(start_col, start_row), (end_col, end_row) = cmd[1], cmd[2]
				span_height = sum(row_heights[start_row:end_row + 1])
				max_height = max(row_heights[start_row:end_row + 1])
				for i in range(start_row, end_row + 1):
					row_heights[i] = 0  # Обнуляем высоты объединенных строк
				row_heights[start_row] = max(span_height, max_height)  # Задаем высоту для первой строки

		total_height = sum(row_heights)
		return total_height

	def generate_test_table(self, *args):
		list_for_test_table = []
		for arg in args:
			list_for_test_table.extend(arg)

		value_for_styles = [row[0] for row in list_for_test_table]
		test_data_row = [row[1:] for row in list_for_test_table]
		test_table = Table(test_data_row, colWidths=self.col_widths_points)
		c_p = [] #8
		c_fb = [] #9
		c_fd = [] #10
		c_rb = [] #11
		c_rd = [] #12

		for i in range(len(value_for_styles)):
			if value_for_styles[i] == 'header':
				test_table.setStyle(TableStyle([
					('GRID', (0, i), (-1, i), 0.5, colors.black),
					('ALIGN', (0, i), (-1, i), 'CENTER'),
					('LEFTPADDING', (0, i), (-1, i), 1),
					('RIGHTPADDING', (0, i), (-1, i), 0),
					('TOPPADDING', (0, i), (-1, i), 0),
					('BOTTOMPADDING', (0, i), (-1, i), 0),
				]))
		
			if value_for_styles[i] == 'brand':
				test_table.setStyle(TableStyle([
					('BACKGROUND', (0, i), (-1, i), colors.darkkhaki),
					('GRID', (0, i), (-1, i), 0.5, colors.black),
					('SPAN', (0, i), (-1, i)),
					('ALIGN', (0, i), (-1, i), 'LEFT'),
					('VALIGN', (0, i), (-1, i), 'MIDDLE'),
					('LEFTPADDING', (0, i), (-1, i), 1),
					('RIGHTPADDING', (0, i), (-1, i), 0),
					('TOPPADDING', (0, i), (-1, i), 0),
					('BOTTOMPADDING', (0, i), (-1, i), 0),
				]))
			
			elif value_for_styles[i] == 'model':
				test_table.setStyle(TableStyle([
					('BACKGROUND', (0, i), (-1, i), colors.lightcoral),
					('GRID', (0, i), (-1, i), 0.5, 'black'),
					('SPAN', (0, i), (-1, i)),
					('ALIGN', (0, i), (-1, i), 'LEFT'),
					('VALIGN', (0, i), (-1, i), 'MIDDLE'),
					('LEFTPADDING', (0, i), (-1, i), 1),
					('RIGHTPADDING', (0, i), (-1, i), 0),
					('TOPPADDING', (0, i), (-1, i), 0),
					('BOTTOMPADDING', (0, i), (-1, i), 0),
				]))
			elif value_for_styles[i] == 'parts':
				test_table.setStyle(TableStyle([
					('BACKGROUND', (0, i), (-1, i), 'rgb(255, 249, 215)'),
					('GRID', (0, i), (-1, i), 0.5, 'black'),
					('VALIGN', (0, i), (-1, i), 'MIDDLE'),
					('LEFTPADDING', (0, i), (-1, i), 0),
					('LEFTPADDING', (2, i), (6, i), 1),
					('RIGHTPADDING', (0, i), (-1, i), 0),
					('TOPPADDING', (0, i), (-1, i), 1),
					('BOTTOMPADDING', (0, i), (-1, i), 1),
				]))

		for a, row in enumerate(list_for_test_table):
			for i, cell in enumerate(row):
				if i == 8: #c_p
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_p:
								test_table.setStyle(TableStyle([
								('SPAN', (i-1, a-len(c_p)), (i-1, a)),
								('GRID', (i-1, a-len(c_p)), (i-1, a), 0.5, 'black'),
								]))
								c_p.append(part_text)
							elif c_p == []:
								c_p.append(part_text)
							else:
								c_p = [part_text]
						else:
							c_p = []
				if i == 9: #c_fb
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_fb:
								test_table.setStyle(TableStyle([
								('SPAN', (i-1, a-len(c_fb)), (i-1, a)),
								('GRID', (i-1, a-len(c_fb)), (i-1, a), 0.5, 'black'),
								]))
								c_fb.append(part_text)
							elif c_fb == []:
								c_fb.append(part_text)
							else:
								c_fb = [part_text]
						else:
							c_fb = []
				if i == 10: #c_fd
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_fd:
								test_table.setStyle(TableStyle([
								('SPAN', (i-1, a-len(c_fd)), (i-1, a)),
								('GRID', (i-1, a-len(c_fd)), (i-1, a), 0.5, 'black'),
								]))
								c_fd.append(part_text)
							elif c_fd == []:
								c_fd.append(part_text)
							else:
								c_fd = [part_text]
						else:
							c_fd = []
				if i == 11: #c_rb
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_rb:
								test_table.setStyle(TableStyle([
								('SPAN', (i-1, a-len(c_rb)), (i-1, a)),
								('GRID', (i-1, a-len(c_rb)), (i-1, a), 0.5, 'black'),
								]))
								c_rb.append(part_text)
							elif c_rb == []:
								c_rb.append(part_text)
							else:
								c_rb = [part_text]
						else:
							c_rb = []
				if i == 12: #c_rd
					if isinstance(cell, Paragraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_rd:
								test_table.setStyle(TableStyle([
								('SPAN', (i-1, a-len(c_rd)), (i-1, a)),
								('GRID', (i-1, a-len(c_rd)), (i-1, a), 0.5, 'black'),
								]))
								c_rd.append(part_text)
							elif c_rd == []:
								c_rd.append(part_text)
							else:
								c_rd = [part_text]
						else:
							c_rd = []

		print(self.calculate_table_height_with_span(test_table))
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
		model_data= [[Paragraph(str(cell), self.parts_style if i in [0, 1, 7, 8, 9, 10, 11] else self.application_style) for i, cell in enumerate(row)] for row in sorted_grouped_df.values]
		return model_data

	def generate_models_in_brand(self, brand_data_row):
		models_in_brand = []
		for cell in brand_data_row:
			if cell[0] not in models_in_brand:
				models_in_brand.append(cell[0])
		return models_in_brand
	
	def generate_header_data(self):
		header_data = ['header'] + [Paragraph(col, self.header_style) for col in self.headers[0]]
		return header_data
	
	def generate_template_list(self):
		list_for_test_table = []
		header_data = self.generate_header_data()
		list_for_test_table.append(header_data)
		return list_for_test_table
	
	def generate_brand_name(self, brand):
		brand_name = ['brand'] + [Paragraph(brand, self.brand_model_style)] + [""] * (len(self.headers[0]) - 1)
		return brand_name
	
	def generate_model_name_row(self, model_name):
		model_name_row = ['model'] + [Paragraph(model_name, self.brand_model_style)] + [""] * (len(self.headers[0]) - 1)
		return model_name_row
	
	def generate_page(self, page_list):
		ended_page = self.generate_test_table(page_list)
		self.table_elements.append(ended_page)
	
	def move_to_next_page(self):
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
					test_table_height = self.get_element_height(test_table)
					while self.height >= test_table_height:
						if not model_data:
							break
						if input_model_name == False:
							model_name_row = self.generate_model_name_row(model_name)
							new_row = ['parts'] + model_data[0] #абсолютно 0 идей почему [new_row] до вызова функции не работает, а во время - работает
							test_table = self.generate_test_table(page_list, [model_name_row], [new_row])
							test_table_height = self.get_element_height(test_table)
							if self.height >= test_table_height:
								model_data.pop(0)
								page_list.append(model_name_row)
								page_list.append(new_row)
								input_model_name = True
							else:
								self.generate_page(page_list)
								self.move_to_next_page()
								page_list = self.generate_template_list()
								ended_page = None
								break
						try:
							new_row = ['parts'] + model_data[0] #абсолютно 0 идей почему [new_row] до вызова функции не работает, а во время - работает
						except IndexError:
							break
						
						test_table = self.generate_test_table(page_list, [new_row])
						test_table_height = self.get_element_height(test_table)
						if self.height >= test_table_height:
							model_data.pop(0)
							page_list.append(new_row)
						else:
							self.generate_page(page_list)
							self.move_to_next_page()
							page_list = self.generate_template_list()
							ended_page = None
							break
			else:
				if ended_page == None:
					self.generate_page(page_list)
					self.move_to_next_page()
					page_list = self.generate_template_list()
		
		doc.build(self.table_elements)


x = GeneratePdf('data/data.csv')
x.generate_pdf_2()