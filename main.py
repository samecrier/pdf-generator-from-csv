import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from collections import defaultdict
from pprint import pprint
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from pdfgenerator.custom_paragraph import CustomParagraph
from pdfgenerator.span_helper import SpanHelper
from pdfgenerator.table_helper import TableHelper
from pdfgenerator.generate_helper import GenerateHelper
from pdfgenerator.variables.styles import StylesHelper
from pdfgenerator.variables.variables import EXCEL_WIDTH_POINTS

import time
pdfmetrics.registerFont(TTFont("Consolas", "fonts/consola.ttf"))
pdfmetrics.registerFont(TTFont("Dejavu", "fonts/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("Calibri", "fonts/calibri.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans", "fonts/NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Meiryo", "fonts/meiryo.ttf"))


class GeneratePdf():

	def __init__(self, csv_file):
		data = pd.read_csv(csv_file, sep=';', keep_default_na=False, dtype=str)
		columns_to_format = ["PARKING", "FRONT BRAKES", "FRONT DISCS", "REAR BRAKES", "REAR DISCS"]
		for col in columns_to_format:
			data[col] = data[col].apply(TableHelper.format_cell_text)
		data['Y_2_transformed'] = data['Y_2'].replace("~", "60.12")
		data['Y_1'] = pd.to_datetime(data.iloc[:, 2], format="%y.%m", errors='coerce')
		data['Y_2'] = pd.to_datetime(data.iloc[:, 3], format="%y.%m", errors='coerce')
		data['Y_2_transformed'] = pd.to_datetime(data.iloc[:, 14], format="%y.%m", errors='coerce')
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
		a4_variable = 829
		self.height = a4_variable - (self.margin_top+self.margin_bottom)

		self.col_widths_points = [w * 0.68 for w in EXCEL_WIDTH_POINTS]
		self.page_counter = 1
		self.table_elements = []
		self.available_height = self.height


	def timer(func):
		def wrapper(*args, **kwargs):
			start_time = time.time()  # Засекаем время начала выполнения
			result = func(*args, **kwargs)
			end_time = time.time()    # Засекаем время завершения
			elapsed_time = end_time - start_time
			print(f"Function '{func.__name__}' executed in {elapsed_time:.4f} seconds")
			return result
		return wrapper
	
	def create_doc(self, output_file):
		doc = SimpleDocTemplate(
			output_file,
			pagesize=A4,
			topMargin=self.margin_top,
			bottomMargin=self.margin_bottom)
		return doc
	
	def generate_page(self, helper, page_list, height_to_increase, table_row_heights):
		ended_page = helper.generate_test_table(page_list, height_to_increase=height_to_increase, table_row_heights=table_row_heights)
		self.table_elements.append(ended_page)
	
	def move_to_next_page(self):
		self.page_counter += 1
		print(f"Перехожу на страницу {self.page_counter}")
		self.table_elements.append(PageBreak())
		helper = GenerateHelper()
		return helper
	@timer
	def generate_pdf_2(self):
		doc = self.create_doc('pdf/draft_mock.pdf')
		helper = GenerateHelper()
		for brand in self.brands_dict:
			brand_data_row = self.brands_dict[brand]
			models_in_brand = helper.generate_models_in_brand(brand_data_row)
			
			input_brand_name = False
			model_data = None
			ended_page = None

			page_list = helper.generate_template_list()

			while models_in_brand:
				if input_brand_name == False:
					brand_name = helper.generate_brand_name(brand)
					page_list.append(brand_name)
					input_brand_name = True
				if models_in_brand:
					model_name = models_in_brand.pop(0)
				else:
					break
				
				if not model_data:
					current_model = TableHelper.get_models(brand_data_row, model_name)
					model_data = helper.generate_grouped_model_data(current_model)

				while model_data:
					input_model_name = False
					test_table = helper.generate_test_table(page_list)
					test_table_height, table_row_heights = TableHelper.calc_height_span(test_table, helper.commands)
					while self.height >= test_table_height:
						if not model_data:
							break
						if input_model_name == False:
							model_name_row = helper.generate_model_name_row(model_name)
							new_row = ['parts'] + model_data[0] #абсолютно 0 идей почему [new_row] до вызова функции не работает, а во время - работает
							test_table = helper.generate_test_table(page_list, [model_name_row], [new_row])
							test_table_height, table_row_heights = TableHelper.calc_height_span(test_table, helper.commands)
							if self.height >= test_table_height:
								model_data.pop(0)
								page_list.append(model_name_row)
								page_list.append(new_row)
								input_model_name = True
							else:
								test_table = helper.generate_test_table(page_list)
								test_table_height, table_row_heights = TableHelper.calc_height_span(test_table, helper.commands)
								height_to_increase = self.height - test_table_height
								# print(f"увеличить {height_to_increase} height {self.height} test_table {test_table_height}")
								self.generate_page(helper, page_list, height_to_increase, table_row_heights)
								helper = self.move_to_next_page()
								page_list = helper.generate_template_list()
								ended_page = None
								break
						try:
							new_row = ['parts'] + model_data[0] #абсолютно 0 идей почему [new_row] до вызова функции не работает, а во время - работает
						except IndexError:
							break
						
						test_table = helper.generate_test_table(page_list, [new_row])
						test_table_height, table_row_heights = TableHelper.calc_height_span(test_table, helper.commands)
						# print('check new row', model_name, self.height, test_table_height)
						if self.height >= test_table_height:
							# print(f"if self height after check {model_name}")
							model_data.pop(0)
							page_list.append(new_row)
						else:
							test_table = helper.generate_test_table(page_list)
							test_table_height, table_row_heights = TableHelper.calc_height_span(test_table, helper.commands)
							height_to_increase = self.height - test_table_height
							# print(f"увеличить {height_to_increase} height {self.height} test_table {test_table_height}")
							self.generate_page(helper, page_list, height_to_increase, table_row_heights)
							helper = self.move_to_next_page()
							page_list = helper.generate_template_list()
							ended_page = None
							break
			else:
				if ended_page == None:
					height_to_increase=self.height-test_table_height
					# print(height_to_increase)
					# self.generate_page(helper, page_list, height_to_increase=height_to_increase, table_row_heights=table_row_heights)
					self.generate_page(helper, page_list, height_to_increase=0, table_row_heights=table_row_heights)
					helper = self.move_to_next_page()
					page_list = helper.generate_template_list()

		doc.build(self.table_elements)

if __name__ == '__main__':
	x = GeneratePdf('data/data.csv')
	x.generate_pdf_2()