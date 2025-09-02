FROM apache/spark:3.5.4

USER root

ADD https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar
ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar /opt/spark/jars/hadoop-aws-3.3.4.jar
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-connect_2.12/3.5.4/spark-connect_2.12-3.5.4.jar /opt/spark/jars/spark-connect_2.12-3.5.4.jar
ADD https://jdbc.postgresql.org/download/postgresql-42.7.5.jar /opt/spark/jars/postgresql-42.7.5.jar

RUN chmod -R +r /opt/spark/jars

USER spark
