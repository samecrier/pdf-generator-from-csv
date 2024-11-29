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
			'YEAR',
			'YEAR',
			'APPLICATION',
			'ENGINE',
			'APP_1',
			'APP_2',
			'APP_3',
			'PARKING',
			'FRONT <br />BRAKES',
			'FRONT <br />DISCS',
			'REAR <br />BRAKES ',
			'REAR <br />DISCS']]
		self.col_widths_points = [w * 0.68 for w in EXCEL_WIDTH_POINTS]

	def styles_for_column(self, i):
		if i in [2, 3]:
			return self.styles.application_center_style
		if i in [4, 5, 6]:
			return self.styles.application_style
		else:
			# print(type(self.parts_style))
			return self.styles.parts_style
		
	def body_cell_edit(self, cell):
		formatted_cell = sorted({x.strip() for word in cell for x in word.split(',') if word != ''})
		return ',<br />'.join(formatted_cell)  # Объединяем с помощью <br />
	
	def engine_cell_edit(self, cell):
		formatted_cell = sorted({x.strip() for word in cell for x in word.split(',') if word !=''})
		return '<br />'.join(formatted_cell)  # Объединяем с помощью <br />
	
	def app_first(self, cell):
		formatted_cell = sorted({word.strip() for word in cell if word != ''})
		return '<br />'.join(formatted_cell)  # Объединяем с помощью <br />
	
	@staticmethod
	def generate_models_in_brand(brand_data_row):
		models_in_brand = []
		for cell in brand_data_row:
			if cell[0] not in models_in_brand:
				models_in_brand.append(cell[0])
		return models_in_brand
	
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

		finished_df = df[df['Y_2_transformed'] != '2060-12-01']
		unfinished_df = df[df['Y_2_transformed'] == '2060-12-01']


		grouped_finished = finished_df.groupby(['PARKING', 'FR BR', 'FR DS', 'RR BR', 'RR DS'], as_index=False).agg({
			'Y_1': 'min',
			'Y_2': 'max',
			'Y_2_transformed': 'max',
			'BODY': self.body_cell_edit, 
			'ENGINE': self.engine_cell_edit,
			'APP_1': self.app_first,
			'APP_2': lambda x: '<br />'.join(sorted(set(filter(None, x)))),
			'APP_3': lambda x: '<br />'.join(sorted(set(filter(None, x)))),
			'PARKING': 'first',
			'FR BR': 'first',
			'FR DS': 'first',
			'RR BR': 'first',
			'RR DS': 'first'
		})

		grouped_unfinished = unfinished_df.groupby(['PARKING', 'FR BR', 'FR DS', 'RR BR', 'RR DS', 'Y_1', 'Y_2_transformed'], as_index=False).agg({
			'Y_1': 'min',
			'Y_2': 'max',
			'Y_2_transformed': 'max',
			'BODY': self.body_cell_edit, 
			'ENGINE': self.engine_cell_edit,
			'APP_1': self.app_first,
			'APP_2': lambda x: '<br />'.join(sorted(set(filter(None, x)))),
			'APP_3': lambda x: '<br />'.join(sorted(set(filter(None, x)))),
			'PARKING': 'first',
			'FR BR': 'first',
			'FR DS': 'first',
			'RR BR': 'first',
			'RR DS': 'first'
		})

		grouped_df = pd.concat([grouped_finished, grouped_unfinished], ignore_index=True)
		# print(grouped_df)
		#ЭТОТ КОД ПРАВИЛЬНО ДЕЛАЕТ ВКЛАДКУ С ПРИУСОМ
		# grouped_df = df.sort_values(by=['Y_1'])
		# body_priority = df.groupby('BODY')['Y_1'].transform('min')
		# grouped_df['PRIORITY'] = body_priority
		# sorted_grouped_df = grouped_df.sort_values(by=['PRIORITY', 'BODY', 'Y_1', 'Y_2_transformed', 'APP_3'], ascending=[True, True, True, True, True])
		# sorted_grouped_df = sorted_grouped_df.drop(columns='PRIORITY').reset_index(drop=True)
		
		grouped_df = grouped_df.sort_values(by=['Y_1'])
		body_priority = grouped_df.groupby('BODY')['Y_1'].transform('min')
		grouped_df['BODY_PRIORITY'] = body_priority
		grouped_df['ENGINE_PRIORITY'] = grouped_df.groupby('BODY')['ENGINE'].transform(lambda x: pd.factorize(x)[0])
		sorted_grouped_df = grouped_df.sort_values(by=['BODY_PRIORITY', 'BODY', 'ENGINE_PRIORITY', 'Y_1', 'Y_2_transformed', 'APP_3'], ascending=[True, True, True, True, True, True])
		sorted_grouped_df = sorted_grouped_df.drop(columns=['BODY_PRIORITY', 'ENGINE_PRIORITY']).reset_index(drop=True)

		sorted_grouped_df['Y_1'] = sorted_grouped_df['Y_1'].dt.strftime('%y.%m')
		sorted_grouped_df['Y_2'] = sorted_grouped_df['Y_2_transformed'].apply(
			lambda x: '~' if x == pd.Timestamp('2060-12-01') else x.strftime("%y.%m")
		)
		sorted_grouped_df = sorted_grouped_df.drop(columns=['Y_2_transformed'])
		sorted_grouped_df.rename(columns={'Y_1': 'YEAR', 'Y_2': 'YEAR'}, inplace=True)
		
		sorted_grouped_df = sorted_grouped_df.groupby(['BODY', 'ENGINE'], group_keys=False).apply(TableHelper.edit_app_three)
		
		model_data= [
			[CustomParagraph(str(cell), 
			self.styles_for_column(i), 
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
		span_width = sum(self.col_widths_points[2:7])
		header_data = ['header'] + [CustomParagraph(
			col, 
			self.styles.header_style,
			default_width=span_width if i == 3 else self.col_widths_points[i],
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