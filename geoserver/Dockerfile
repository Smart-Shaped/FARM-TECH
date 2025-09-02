FROM docker.osgeo.org/geoserver:2.25.x

# Scarica e installa il plugin S3-GeoTIFF
# ADD https://build.geoserver.org/geoserver/2.24.x/community-latest/geoserver-2.24-SNAPSHOT-s3-geotiff-plugin.zip /tmp/

# RUN unzip -o /tmp/geoserver-2.24-SNAPSHOT-s3-geotiff-plugin.zip -d /usr/local/tomcat/webapps/geoserver/WEB-INF/lib/ && \
#     rm /tmp/geoserver-2.24-SNAPSHOT-s3-geotiff-plugin.zip

ADD https://repo1.maven.org/maven2/net/sf/ehcache/ehcache/2.10.9.2/ehcache-2.10.9.2.jar /usr/local/tomcat/webapps/geoserver/WEB-INF/lib/
