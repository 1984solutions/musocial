docker run -d -e VIRTUAL_HOST=musocial.me --network=webproxy --name=musocial -e LETSENCRYPT_HOST=musocial.me -e LETSENCRYPT_EMAIL=musocial@ibz.me -v $(pwd)/db:/db -v $(pwd)/instance-docker:/instance ibz0/musocial