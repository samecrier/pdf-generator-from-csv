import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from collections import defaultdict

class GeneratePdf():
	
	PADDING_ZERO = [
		('LEFTPADDING', (0, 0), (-1, -1), 0),
		('RIGHTPADDING', (0, 0), (-1, -1), 0),
		('TOPPADDING', (0, 0), (-1, -1), 0),
		('BOTTOMPADDING', (0, 0), (-1, -1), 0),
	]


	def __init__(self, csv_file):
		data = pd.read_csv(csv_file, sep=';', keep_default_na=False, dtype=str)
		data['Y_1'] = pd.to_datetime(data.iloc[:, 3], format="%y.%m", errors='coerce')
		data['Y_2'] = pd.to_datetime(data.iloc[:, 4], format="%y.%m", errors='coerce')
		
		self.headers = [data.columns.tolist()[3:]]
		values = data.values.tolist()
		self.brands_dict = defaultdict(lambda: defaultdict(list))
		
		for value in values:
			brand = value[0]
			model_id = value[1]
			data = value[2:]
			self.brands_dict[brand][model_id].append(data)
		
		self.margin_top = 10
		self.margin_bottom = 20
		# a4_variable = A4[1] - не учитывает отступы SimpleDocTemplete
		a4_variable = 829
		self.height = a4_variable - (self.margin_top+self.margin_bottom)

		excel_widths_pixels = [42, 42, 78, 72, 64, 39, 89, 71, 90, 90, 90, 90]
		self.col_widths_points = [w * 0.68 for w in excel_widths_pixels]

		self.elements = []
		self.available_height = self.height
		self.current_height = 0

		self.styles = getSampleStyleSheet()
		self.initialize_styles()
		
		
		
		# self.styles["Normal"].fontSize = 8  # Задаем размер шрифта для всех параграфов со стилем "Normal"
		# self.styles["Normal"].leading = 8  #
		# self.style_normal = self.styles["Normal"]
		# self.style_normal.alignment = TA_CENTER

	def initialize_styles(self):
		self.header_style = self.styles["Normal"].clone('Header')
		
		self.brand_model_style = self.styles["Normal"].clone('Brand')
		self.brand_style = self.styles["Normal"].clone('Brand')
		self.model_style = self.styles["Normal"].clone('Model')
		
		self.main_style = self.styles["Normal"].clone('Main')
		self.years_style = self.styles["Normal"].clone('Years')
		self.application_style = self.styles["Normal"].clone('App')
		self.application_option_style = self.styles["Normal"].clone('AppOption')
		self.application_option2_style = self.styles["Normal"].clone('AppOption2')
		self.parts_style = self.styles["Normal"].clone('Parts')
		self.parts_option_style = self.styles["Normal"].clone('PartsOpt')
		self.parts_option2_style = self.styles["Normal"].clone('PartsOpt2')

	
	def get_element_height(self, element):
		width, height = element.wrap(0, 0)
		return height
	
	def check_element_fits(self, element, available_height):
		""" Проверяет, помещается ли элемент в доступное пространство. """
		width, height = element.wrap(0, available_height)
		return height, height <= available_height

	def create_doc(self, output_file):
		doc = SimpleDocTemplate(
			output_file,
			pagesize=A4,
			topMargin=self.margin_top,
			bottomMargin=self.margin_bottom)
		return doc
	
	def generate_header_table(self):
		header_table = Table(self.headers, colWidths=self.col_widths_points)
		header_table.setStyle(TableStyle([
			('GRID', (0, 0), (-1, -1), 0.5, colors.black),
			('BACKGROUND', (0, 0), (-1, 0), colors.grey),
			('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			*self.PADDING_ZERO
		]))
		
		return header_table

	def generate_brand_table(self, brand):
		brand_list = [Paragraph(brand, self.brand_model_style)] + [""] * (len(self.headers[0]) - 1)
		brand_table = Table([brand_list], colWidths=self.col_widths_points)
		brand_table.setStyle(TableStyle([
			('SPAN', (0, 0), (-1, -1)),
			('BACKGROUND', (0, 0), (-1, 0), colors.darkkhaki),
			('ALIGN', (0, 0), (-1, -1), 'LEFT'),
			('GRID', (0, 0), (-1, -1), 0.5, colors.black),
			*self.PADDING_ZERO
		]))
		return brand_table

	def generate_model_name_row(self, model):
		model_name_row = [Paragraph(model, self.brand_model_style)] + [""] * (len(self.headers[0]) - 1)
		return model_name_row

	def generate_model_data_row(self, model_list):

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
		model_data_row = [[Paragraph(str(cell), self.main_style) for cell in row] for row in sorted_grouped_df.values]
		return model_data_row

	def generate_model_table(self, model_name_row, model_data_row):
		model_rows = model_name_row + model_data_row
		model_table = Table(model_rows, colWidths=self.col_widths_points)
		model_table.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
			('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
			('BACKGROUND', (0, 1), (-1, -1), 'rgb(255, 249, 215)'),
			('SPAN', (0, 0), (-1, 0)),
			('GRID', (0, 0), (-1, -1), 0.5, 'black'),
			*self.PADDING_ZERO
		]))
		return model_table
	
	def generate_separated_model_table(self, model_name_row, model_data_row):
		counter_of_rows = 0
		rows_in_model = len(model_data_row)
		while counter_of_rows <= rows_in_model:
			separated_list_1 = model_data_row[0:counter_of_rows+1]
			separated_model_table_mock = self.generate_model_table(model_name_row, separated_list_1)
			height_separated_model_table_mock = self.get_element_height(separated_model_table_mock)
			
			if self.available_height-height_separated_model_table_mock >= 0:
				separated_model_table = separated_model_table_mock
				counter_of_rows += 1
			else:
				print(model_data_row[counter_of_rows][0].text, model_data_row[counter_of_rows][1].text, model_data_row[counter_of_rows][2].text, model_data_row[counter_of_rows][5].text)
				break
		
		if counter_of_rows == 0:
			separated_model_table = None
		
		list_for_separate = model_data_row[counter_of_rows:]
		
		return separated_model_table, list_for_separate
	
	def generate_next_page(self):
		self.elements.append(PageBreak())
		self.available_height = self.height
		self.generate_header()

	def generate_header(self):
		# Создаю заголовок таблицы
		header_table = self.generate_header_table()
		height_header_table = self.get_element_height(header_table)
		print(f'Доступно: {self.available_height}, станет после header {self.available_height-height_header_table}')
		self.available_height = self.available_height-height_header_table
		self.elements.append(header_table)
		
	def generate_pdf(self):
		
		doc = self.create_doc('pdf/new_mock.pdf')
		self.generate_header()
		
		# Создаю строку с брендом
		for i, brand in enumerate(self.brands_dict):
			brand_table = self.generate_brand_table(brand)
			height_brand_table = self.get_element_height(brand_table)
			print(f'Доступно: {self.available_height}, станет после brand {self.available_height-height_brand_table}')
			self.available_height = self.available_height-height_brand_table
			self.elements.append(brand_table)

			for model_id in self.brands_dict[brand]:
				rows_from_model = self.brands_dict[brand][model_id] #list in list все строки модели(180SX, PRIUS etc)
				model_name = rows_from_model[0][0] #str название модели (180SX, PRIUS)
				
				model_name_row = [self.generate_model_name_row(model_name)] #list in list 1 строка с моделью
				model_data_row = self.generate_model_data_row(rows_from_model) # list in list со строками из модели
				model_table = self.generate_model_table(model_name_row, model_data_row) #сгененированная таблица названия модели + вся строки с модели

				height_model_table = self.get_element_height(model_table)
				print(f'Доступно: {self.available_height}, станет после {model_name} {self.available_height-height_model_table}')
				
				
				if self.available_height-height_model_table >= 0:
					self.elements.append(model_table)
					self.available_height = self.available_height-height_model_table
				elif self.available_height-height_model_table < 0:
					list_for_separate = model_data_row[:]
					while list_for_separate:
						model_table_1, list_for_separate = self.generate_separated_model_table(model_name_row, list_for_separate)
						if model_table_1:
							self.elements.append(model_table_1)
							height_model_table_1 = self.get_element_height(model_table_1)
							self.available_height = self.available_height-height_model_table_1
						if list_for_separate:
							self.generate_next_page()
			
			if i < len(self.brands_dict)-1:
				self.generate_next_page()
		
		doc.build(self.elements)

x = GeneratePdf('data/data.csv')
x.generate_pdf()