from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class StylesHelper():

	HEADER_TOPPADDING = 1
	HEADER_BOTTOMPADDING = 1
	HEADER_LEFTPADDING = 1
	HEADER_RIGHTPADDING = 0

	BRAND_MODEL_TOPPADDING = 1
	BRAND_MODEL_BOTTOMPADDING = 1
	BRAND_MODEL_LEFTPADDING = 1
	BRAND_MODEL_RIGHTPADDING = 0

	APPLICATION_LEFTPADDING = 1
	APPLICATION_RIGHTPADDING = 1
	PARTS_TOPPADDING = 1
	PARTS_BOTTOMPADDING = 1

	def __init__(self):
		self.styles = getSampleStyleSheet()
		self.styles["Normal"].fontSize = 8
		self.styles["Normal"].leading = 10
		self.styles['Normal'].fontName = 'Helvetica'

	@property
	def header_style(self):
		header_style = self.styles["Normal"].clone('Header')
		header_style.alignment = TA_CENTER
		header_style.fontSize = 8
		header_style.leading = 10
		return header_style

	@property
	def brand_model_style(self):
		brand_model_style = self.styles["Normal"].clone('Brand')
		brand_model_style.splitLongWords = False
		# self.brand_model_style.fontSize = 8
		# self.brand_model_style.leading = 10
		return brand_model_style

	@property
	def application_style(self):
		application_style = self.styles["Normal"].clone('App')
		application_style.alignment = TA_LEFT
		# self.application_style.wordWrap = 'CJK'
		return application_style

	@property
	def application_center_style(self):
		application_style = self.styles["Normal"].clone('App')
		application_style.alignment = TA_CENTER
		return application_style

	@property
	def parts_style(self):
		parts_style = self.styles["Normal"].clone('Parts')
		parts_style.alignment = TA_CENTER
		return parts_style
	