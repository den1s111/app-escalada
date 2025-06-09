from django.db import models


class Crag(models.Model):
    nom = models.CharField(max_length=255, primary_key=True)
    localitzacio = models.TextField(blank=True, null=True)
    descripcio = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crag'

    def __str__(self):
        return self.nom


class Sector(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    nom_crag = models.ForeignKey(Crag, on_delete=models.CASCADE, db_column='nom_crag')
    descripcio = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sector'
        unique_together = (('nom', 'nom_crag'),)

    def __str__(self):
        return f"{self.nom} ({self.nom_crag.nom})"



class Via(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    nom_sector = models.ForeignKey(Sector, on_delete=models.CASCADE, db_column='nom_sector')
    nom_crag_sector = models.CharField(max_length=255)
    descripcio = models.TextField(blank=True, null=True)
    grau_dificultat = models.CharField(max_length=50, blank=True, null=True)
    estil = models.CharField(max_length=100, blank=True, null=True)
    alcada_aproximada_metres = models.IntegerField(blank=True, null=True)
    equipador = models.CharField(max_length=255, blank=True, null=True)
    data_equipament = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'via'
        unique_together = (('nom', 'nom_sector', 'nom_crag_sector'),)

    def __str__(self):
        return f"{self.nom} ({self.nom_sector.nom})"



class Escalador(models.Model):
    nom_usuari = models.CharField(max_length=100, primary_key=True)
    contrasenya = models.CharField(max_length=255)
    data_naixement = models.DateField(blank=True, null=True)
    nivell = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'escalador'

    def __str__(self):
        return self.nom_usuari


class Intent(models.Model):
    id_intent = models.AutoField(primary_key=True)
    tipus_ascensio = models.CharField(max_length=100, blank=True, null=True)
    data_intent = models.DateField(blank=False)
    nom_usuari_escalador = models.ForeignKey(Escalador, on_delete=models.CASCADE, db_column='nom_usuari_escalador')
    nom_via = models.CharField(max_length=255)
    nom_sector_via = models.CharField(max_length=255)
    nom_crag_via = models.CharField(max_length=255)

    class Meta:
        db_table = 'intent'
        unique_together = (
            'nom_usuari_escalador',
            'nom_via',
            'nom_sector_via',
            'nom_crag_via',
            'data_intent',
            'tipus_ascensio',
        )

    def __str__(self):
        return f"Intent {self.id_intent} - {self.nom_usuari_escalador}"


class Encadenament(models.Model):
    id_intent = models.OneToOneField(Intent, on_delete=models.CASCADE, db_column='id_intent', primary_key=True)
    temps_ascensio = models.DurationField(blank=True, null=True)

    class Meta:
        db_table = 'encadenament'

    def __str__(self):
        return f"Encadenament Intent {self.id_intent_id}"


class Comentari(models.Model):
    id_comentari = models.AutoField(primary_key=True)
    text_comentari = models.TextField()
    data_comentari = models.DateTimeField(auto_now_add=True)
    nom_usuari_escalador = models.ForeignKey(
        Escalador,
        on_delete=models.SET_NULL,
        db_column='nom_usuari_escalador',
        null=True,
        blank=True,
    )
    nom_via = models.CharField(max_length=255)
    nom_sector_via = models.CharField(max_length=255)
    nom_crag_via = models.CharField(max_length=255)

    class Meta:
        db_table = 'comentari'

    def __str__(self):
        return f"Comentari {self.id_comentari} de {self.nom_usuari_escalador}"


class Recomanacio(models.Model):
    id_recomanacio = models.AutoField(primary_key=True)
    puntuacio = models.SmallIntegerField(null=True, blank=True)
    descripcio_recomanacio = models.TextField(blank=True, null=True)
    data_recomanacio = models.DateTimeField(auto_now_add=True)
    nom_usuari_escalador = models.ForeignKey(
        Escalador,
        on_delete=models.SET_NULL,
        db_column='nom_usuari_escalador',
        null=True,
        blank=True,
    )
    nom_via = models.CharField(max_length=255)
    nom_sector_via = models.CharField(max_length=255)
    nom_crag_via = models.CharField(max_length=255)

    class Meta:
        db_table = 'recomanacio'
        unique_together = (('nom_usuari_escalador', 'nom_via', 'nom_sector_via', 'nom_crag_via'),)

    def __str__(self):
        return f"Recomanacio {self.id_recomanacio} de {self.nom_usuari_escalador}"
