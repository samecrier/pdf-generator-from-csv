from pdfgenerator.span_helper import SpanHelper
from pdfgenerator.custom_paragraph import CustomParagraph
from pdfgenerator.variables.styles import StylesHelper
from reportlab.lib import colors
class TableHelper:

	@staticmethod
	def height_to_guideline(height_to_increase, table_row_heights, value_for_styles):
		'''
		Принимает высоту на которую надо увеличить строки, чтобы заполнить страницу
		Возвращает список с готовыми значениями высоты для каждой строки страницы
		'''
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
		# print(f"sum {sum(final_table_row_heights)} {final_table_row_heights}")
		
		return final_table_row_heights
	
	@staticmethod
	def calc_height_span(table, commands):
		"""
		Рассчитывает высоту таблицы с учетом вертикального объединения (SPAN) и отступов (PADDINGTOP, PADDINGBOTTOM),
		если все содержимое таблицы обернуто в Paragraph.
		"""
		row_heights = [0] * len(table._cellvalues)  # Для сохранения высот строк
		spans = {}
		# Сбор данных о PADDINGTOP и PADDINGBOTTOM
		for cmd in commands:
			if cmd[0] == 'SPAN':
				(start_col, start_row), (end_col, end_row) = cmd[1], cmd[2]
				spans[(start_col, start_row)] = (end_col, end_row)

		max_height_result = SpanHelper.get_max_heights_no_span(table._cellvalues, spans)
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
						span_lines = SpanHelper.get_span_lines(row_idx, col_idx, spans)
						span_rows = SpanHelper.get_span_rows(row_idx, col_idx, spans)
						span_rows_height, span_max = SpanHelper.get_height_span_rows(max_height_result, span_rows)
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
		
		# print(f"sum {sum(row_heights)} {row_heights}")
		total_height = sum(row_heights)
		return total_height, row_heights
	
	@staticmethod
	def get_models(data_row, model_name):
		if data_row:
			current_model = []
			for i, cell in enumerate(data_row):
				if cell[0] == model_name:
					current_model.append(data_row[i])
		else:
			current_model = None
		return current_model
	
	@staticmethod
	def get_commands(value_for_styles, list_for_test_table):
		
		styles = StylesHelper()
		commands = []

		c_p = [] #8
		c_fb = [] #9
		c_fd = [] #10
		c_rb = [] #11
		c_rd = [] #12

		for i in range(len(value_for_styles)):
			if value_for_styles[i] == 'header':
				commands.append(('GRID', (0, i), (-1, i), 0.5, colors.black))
				commands.append(('ALIGN', (0, i), (-1, i), 'CENTER'))
				commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				commands.append(('LEFTPADDING', (0, i), (-1, i), 1))
				commands.append(('RIGHTPADDING', (0, i), (-1, i), 0))
				commands.append(('TOPPADDING', (0, i), (-1, i), 0))
				commands.append(('BOTTOMPADDING', (0, i), (-1, i), 0))
			elif value_for_styles[i] == 'brand':
				commands.append(('BACKGROUND', (0, i), (-1, i), colors.darkkhaki))
				commands.append(('GRID', (0, i), (-1, i), 0.5, colors.black))
				commands.append(('SPAN', (0, i), (-1, i)))
				commands.append(('ALIGN', (0, i), (-1, i), 'LEFT'))
				commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				commands.append(('LEFTPADDING', (0, i), (-1, i), 1))
				commands.append(('RIGHTPADDING', (0, i), (-1, i), 0))
				commands.append(('TOPPADDING', (0, i), (-1, i), 0))
				commands.append(('BOTTOMPADDING', (0, i), (-1, i), 0))
			elif value_for_styles[i] == 'model':
				commands.append(('BACKGROUND', (0, i), (-1, i), colors.lightcoral))
				commands.append(('GRID', (0, i), (-1, i), 0.5, 'black'))
				commands.append(('SPAN', (0, i), (-1, i)))
				commands.append(('ALIGN', (0, i), (-1, i), 'LEFT'))
				commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				commands.append(('LEFTPADDING', (0, i), (-1, i), 1))
				commands.append(('RIGHTPADDING', (0, i), (-1, i), 0))
				commands.append(('TOPPADDING', (0, i), (-1, i), 0))
				commands.append(('BOTTOMPADDING', (0, i), (-1, i), 0))
			elif value_for_styles[i] == 'parts':
				commands.append(('BACKGROUND', (0, i), (-1, i), 'rgb(255, 249, 215)'))
				commands.append(('GRID', (0, i), (-1, i), 0.5, 'black'))
				commands.append(('VALIGN', (0, i), (-1, i), 'MIDDLE'))
				commands.append(('LEFTPADDING', (0, i), (-1, i), 0))
				commands.append(('LEFTPADDING', (2, i), (6, i), styles.APPLICATION_LEFTPADDING))
				commands.append(('RIGHTPADDING', (0, i), (-1, i), styles.APPLICATION_RIGHTPADDING))
				commands.append(('TOPPADDING', (0, i), (-1, i), styles.PARTS_TOPPADDING))
				commands.append(('BOTTOMPADDING', (0, i), (-1, i), styles.PARTS_BOTTOMPADDING))

		for a, row in enumerate(list_for_test_table):
			for i, cell in enumerate(row):
				if i == 8: #c_p
					if isinstance(cell, CustomParagraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_p:
								commands.append(('SPAN', (i-1, a-len(c_p)), (i-1, a)))
								commands.append(('GRID', (i-1, a-len(c_p)), (i-1, a), 0.5, 'black'))
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
					if isinstance(cell, CustomParagraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_fb:
								commands.append(('SPAN', (i-1, a-len(c_fb)), (i-1, a)))
								commands.append(('GRID', (i-1, a-len(c_fb)), (i-1, a), 0.5, 'black'))
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
					if isinstance(cell, CustomParagraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_fd:
								commands.append(('SPAN', (i-1, a-len(c_fd)), (i-1, a)))
								commands.append(('GRID', (i-1, a-len(c_fd)), (i-1, a), 0.5, 'black'))
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
					if isinstance(cell, CustomParagraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_rb:
								commands.append(('SPAN', (i-1, a-len(c_rb)), (i-1, a)))
								commands.append(('GRID', (i-1, a-len(c_rb)), (i-1, a), 0.5, 'black'))
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
					if isinstance(cell, CustomParagraph):
						part_text = list_for_test_table[a][i].text
						if part_text != '':
							if part_text in c_rd:
								commands.append(('SPAN', (i-1, a-len(c_rd)), (i-1, a)))
								commands.append(('GRID', (i-1, a-len(c_rd)), (i-1, a), 0.5, 'black'))
								c_rd.append(part_text)
							elif c_rd == []:
								c_rd.append(part_text)
							else:
								c_rd = [part_text]
						else:
							c_rd = []
					else:
						c_rd = []
		
		return commands
	
	@staticmethod
	def format_cell_text(text):
		# Разделяем текст по пробелам
		words = str(text).split()
		formatted_lines = []
		current_line = ''

		for i, word in enumerate(words):
			# Если слово начинается с "GS-", "GP-", "GD-", "GR-"
			if word.startswith(("GS-", "GP-", "GD-", "GR-", 'N/A')) or (
				word.startswith('|') and word.endswith('|')
				):
				# Завершаем текущую строку, если она не пуста
				if current_line:
					current_line = current_line + '<br />'
					formatted_lines.append(current_line)
				else:
					if formatted_lines != []:
						if '<br />' not in formatted_lines[-1]:
							formatted_lines.append('<br />')
				current_line = word
			elif word == "or" and i > 0 and words[i - 1].startswith(("GS-", "GP-", "GD-", "GR-")):
				# Если это "or" и оно следует после указанных префиксов
				current_line = current_line + ' ' + word + '<br />'
				formatted_lines.append(current_line)
				current_line = ''
			else:
				# Если это другой текст
				if current_line:
					current_line = current_line + '<br />'
					formatted_lines.append(current_line)
					current_line = ''
				formatted_lines.append(word)

		# Добавляем оставшийся текст
		if current_line:
			formatted_lines.append(word)

		return ' '.join(formatted_lines)