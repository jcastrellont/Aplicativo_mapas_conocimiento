# Aplicativo para la construcción de mapas de conocimiento

El presente ejecutable permite construir el mapa de conocimiento que ofrece una visualización de los temas más relevantes en una área de conocimiento particular. Esta herramienta tiene como insumos:

1. **El nombre del área del conocimiento que se quiere investigar:** Esta herramienta obtendrá información relevante de los artículos que se publicaron en la plataforma Arxiv (https://arxiv.org/) relacionados al tema de busqueda.
   
2. **Fecha inicial:** Permite al usuario seleccionar las fechas de publicación de estos artículos en los que está interesado. La fecha inicial es la fecha del artículo más antiguo en el que esté interesado el usuario.

3. **Fecha final:** Es la fecha del artículo más nuevo en el que esté interesado el usuario.

4. **Máximo de resultados:** Este insumo permite al usuario filtrar por el número total de artículos a considerar. Por cuestión de recursos y de permisos con la plataforma de Arxiv, se recomienda que este valor no sea superior a los 2000

5. **Nombre del mapa:** La salida de este ejecutable, es una imagen .png que contiene el mapa de conocimiento construido y que será guardada en la misma carpeta donde quede instalada esta herramienta en su computador local. Por está razón se pide el nombre del mapa para que quede almacenado.
