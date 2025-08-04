from mordecai3 import Geoparser

geo = Geoparser()

text = "Protests were held in Alexanderplatz in Berlin."

result = geo.geoparse_doc(text)

print(result)
