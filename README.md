# PDF Compressor

Necessário actualizar no template "templates/base_template.html":

- Imagem do banner de cima neste momento é da Digital Signature, é portanto necessário substituir.
- Texto no fim da página, substituir ou remover completamente.



Recursos Azure:
- Container Registry (https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-portal#create-a-container-registry)
- Web App for Containers (https://docs.microsoft.com/en-us/azure/devops/pipelines/apps/cd/deploy-docker-webapp?view=azure-devops&tabs=java)

Para correr a aplicação e fazer o deploy para azure é necessário primeiro criar a imagem do container, correndo por exemplo o comando (é necessário ter o Docker instalado):

 docker build -t mybuildimage
 
Para puxar a imagem para o Azure, pode-se seguir a seguinte documentação da microsoft: https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-docker-cli?tabs=azure-cli
