
´´´
src/
    app/
        controllers/    # Controladores para lógica das rotas
        database/       # Conexões e migrações do banco de dados
        middlewares/    # Middlewares para interceptação de requisições
        models/         # Definição dos modelos (ORM)
        proto/          # Arquivos protobuf
        provider/       # Serviços de configuração e injeção de dependências
        routes/         # Definição de rotas e Blueprint
        services/       # Lógica de negócio (serviços)
        static/         # Arquivos estáticos (CSS, JS, imagens)
        templates/      # Templates HTML (se aplicável)
    test/
docker_compose.yml
run.py                 # Arquivo de entrada para rodar a aplicação
```

run file proto:

```
  cd .\src\app\proto\
  protoc -I . --python_betterproto_out=./pb/ *.proto
```