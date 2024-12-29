def actualizar_dominios(db, server_id, nuevo_dominio):
    collection = db.collection('servidores').document(server_id).collections()
    for collection_name in collection:
        docs = db.collection(collection_name).stream()
        for doc in docs:
            data = doc.to_dict()
            if "link_ikigai" in data:
                viejo_dominio = data['link_ikigai'].split('/')[2]
                data['link_ikigai'] = data['link_ikigai'].replace(viejo_dominio, nuevo_dominio)
                db.collection(collection_name).document(doc.id).update(data)
