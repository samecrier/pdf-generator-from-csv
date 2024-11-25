class SpanHelper():

	@staticmethod
	def get_height_span_rows(max_height_result, span_rows):
		span_rows_height = 0
		span_max = []
		for row_idx in span_rows:
			span_rows_height += max_height_result[row_idx]
			span_max.append(max_height_result[row_idx])
		return span_rows_height, span_max

	@staticmethod
	def get_span_rows(row_idx, col_idx, spans):
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
	
	@staticmethod
	def get_max_heights_no_span(table_data, spans):
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
	
	@staticmethod
	def get_span_lines(row_idx, col_idx, spans):
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