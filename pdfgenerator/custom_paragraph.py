from reportlab.platypus import Paragraph
from reportlab.pdfbase.pdfmetrics import stringWidth

class CustomParagraph(Paragraph):
	def __init__(self, text, style, default_width=None, 
			leftpadding=0, rightpadding=0, toppadding=0, bottompadding=0):
		
		super().__init__(text, style)
		self.default_width = default_width  # Задаём ширину вручную
		self.leftpadding = leftpadding
		self.rightpadding = rightpadding
		self.toppadding = toppadding
		self.bottompadding = bottompadding
		self.calculated_height = self.calculate_custom_height()
		self.default_height = self.get_default_height()
	
	def calculate_custom_height(self):
		"""
		Пересчитывает высоту текста с учетом реальной ширины.
		"""
		if self.default_width:
			_, self.calculated_height = self.wrap(
				self.default_width-self.leftpadding-self.rightpadding, 
				0)  # Используем wrap для пересчета
			self.calculated_height = self.calculated_height + self.toppadding + self.bottompadding
			
		else:
			self.calculated_height = 0
		return self.calculated_height
	
	def set_width(self, default_width):
		"""
		Обновляет ширину и пересчитывает высоту.
		"""
		self.default_width = default_width
		self.calculate_custom_height()

	def get_height(self):
		"""
		Возвращает пересчитанную высоту.
		"""
		return self.calculated_height

	def count_lines(self):
		"""
		Подсчитывает количество строк в CustomParagraph.
		
		Args:
			custom_paragraph: Объект CustomParagraph.
		
		Returns:
			int: Количество строк.
		"""
		if hasattr(self, 'blPara') and hasattr(self.blPara, 'lines'):
			self.real_rows = len(self.blPara.lines)
		else:
			# Если данные о строках недоступны
			self.real_rows = 0
		return self.real_rows
	
	def get_default_height(self):
		real_rows = self.count_lines()
		if real_rows:
			self.default_height = self.height / real_rows
		else:
			self.default_height = 0
		
		return self.default_height
	
	def set_padding(self, toppadding=0, bottompadding=0):
		"""
		Устанавливает новые значения отступов и пересчитывает высоту.
		"""
		self.toppadding = toppadding
		self.bottompadding = bottompadding
		self.calculate_custom_height()