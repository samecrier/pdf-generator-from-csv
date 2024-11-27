from pdfgenerator.custom_paragraph import CustomParagraph
from pdfgenerator.variables.styles import StylesHelper
from pdfgenerator.table_helper import TableHelper
from pdfgenerator.variables.variables import EXCEL_WIDTH_POINTS
from reportlab.platypus import Table, TableStyle
import pandas as pd

class GenerateHelper:
	
	def __init__(self):
		self.styles = StylesHelper()
		self.headers = [[
			'Y_1',
			'Y_2',
			'BODY',
			'ENGINE',
			'APP_1',
			'APP_2',
			'APP_3',
			'PARKING',
			'FRONT BRAKES',
			'FRONT DISCS',
			'REAR BRAKES ',
			'REAR DISCS']]
		self.col_widths_points = [w * 0.68 for w in EXCEL_WIDTH_POINTS]
	
	def generate_test_table(self, *args, height_to_increase=0, table_row_heights=None):
		list_for_test_table = []
		for arg in args:
			list_for_test_table.extend(arg)

		value_for_styles = [row[0] for row in list_for_test_table]
		test_data_row = [row[1:] for row in list_for_test_table]

		self.commands = TableHelper.get_commands(value_for_styles, list_for_test_table)
		final_table_row_heights = None
		if height_to_increase > 0:
			final_table_row_heights = TableHelper.height_to_guideline(height_to_increase, table_row_heights, value_for_styles)
		
		if final_table_row_heights:
			test_table = Table(test_data_row, colWidths=self.col_widths_points, rowHeights=final_table_row_heights)
		else:
			test_table = Table(test_data_row, colWidths=self.col_widths_points)
		test_table.setStyle(TableStyle(self.commands))

		return test_table


	def generate_grouped_model_data(self, model_list):
		data = {
			'Y_1': [cell[1] for cell in model_list],
			'Y_2': [cell[2] for cell in model_list],
			'Y_2_transformed': [cell[13] for cell in model_list],
			'BODY': [cell[3] for cell in model_list],
			'ENGINE': [cell[4] for cell in model_list],
			'APP_1': [cell[5] for cell in model_list],
			'APP_2': [cell[6] for cell in model_list],
			'APP_3': [cell[7] for cell in model_list],
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
			'Y_2_transformed': 'max',
			'BODY': lambda x: ', '.join(sorted(set(filter(None, x)))), 
			'ENGINE': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'APP_1': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'APP_2': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'APP_3': lambda x: ', '.join(sorted(set(filter(None, x)))),
			'PARKING': 'first',
			'FR BR': 'first',
			'FR DS': 'first',
			'RR BR': 'first',
			'RR DS': 'first'
		})
		sorted_grouped_df = grouped_df.sort_values(by=['Y_1', 'Y_2', 'APP_1'], ascending=[True, True, True])
		sorted_grouped_df['Y_1'] = sorted_grouped_df['Y_1'].dt.strftime('%y.%m')
		sorted_grouped_df['Y_2'] = sorted_grouped_df['Y_2_transformed'].apply(
			lambda x: '~' if x == pd.Timestamp('2060-12-01') else x.strftime("%y.%m")
		)
		sorted_grouped_df = sorted_grouped_df.drop(columns=['Y_2_transformed'])
		
		model_data= [
			[CustomParagraph(str(cell), 
			self.styles.application_style if i in [2, 3, 4, 5, 6] else self.styles.parts_style, 
			default_width=self.col_widths_points[i],
			leftpadding=self.styles.APPLICATION_LEFTPADDING if i in [2, 3, 4, 5, 6] else 0,
			rightpadding=self.styles.APPLICATION_RIGHTPADDING if i in [2, 3, 4, 5, 6] else 0,
			toppadding=self.styles.PARTS_TOPPADDING,
			bottompadding=self.styles.PARTS_BOTTOMPADDING)
			for i, cell in enumerate(row)] 
			for row in sorted_grouped_df.values
		]
		return model_data
	
	def generate_template_list(self):
		list_for_test_table = []
		header_data = self.generate_header_data()
		list_for_test_table.append(header_data)
		return list_for_test_table
	
	
	def generate_header_data(self):
		header_data = ['header'] + [CustomParagraph(
			col, 
			self.styles.header_style,
			default_width=self.col_widths_points[i],
			toppadding=self.styles.HEADER_TOPPADDING,
			bottompadding=self.styles.HEADER_BOTTOMPADDING,
			leftpadding=self.styles.HEADER_LEFTPADDING,
			rightpadding=self.styles.HEADER_RIGHTPADDING)
		for i, col in enumerate(self.headers[0])]
		return header_data
	
	def generate_brand_name(self, brand):
		span_width = sum(self.col_widths_points)  # Рассчитываем ширину объединенной ячейки
		
		# Используем Paragraph вместо обычного Paragraph
		brand_name_Paragraph = CustomParagraph(
			brand, 
			self.styles.brand_model_style, 
			default_width=span_width,
			toppadding = self.styles.BRAND_MODEL_TOPPADDING,
			bottompadding = self.styles.BRAND_MODEL_BOTTOMPADDING,
			leftpadding=self.styles.BRAND_MODEL_LEFTPADDING,
			rightpadding=self.styles.BRAND_MODEL_RIGHTPADDING
			)

		# Возвращаем строку
		brand_name = ['brand', brand_name_Paragraph] + [""] * (len(self.headers[0]) - 1)
		return brand_name
	
	def generate_model_name_row(self, model_name):
		span_width = sum(self.col_widths_points)  # Рассчитываем ширину объединенной ячейки
		
		# Используем Paragraph вместо обычного Paragraph
		model_name_Paragraph = CustomParagraph(
			model_name, 
			self.styles.brand_model_style, 
			default_width=span_width,
			toppadding = self.styles.BRAND_MODEL_TOPPADDING,
			bottompadding = self.styles.BRAND_MODEL_BOTTOMPADDING,
			leftpadding=self.styles.BRAND_MODEL_LEFTPADDING,
			rightpadding=self.styles.BRAND_MODEL_RIGHTPADDING
		)

		# Возвращаем строку
		model_name_row = ['model', model_name_Paragraph] + [""] * (len(self.headers[0]) - 1)
		return model_name_row
	
	
	@staticmethod
	def generate_models_in_brand(brand_data_row):
		models_in_brand = []
		for cell in brand_data_row:
			if cell[0] not in models_in_brand:
				models_in_brand.append(cell[0])
		return models_in_brand
	