from django.db import models


class Comentari(models.Model):
    id_comentari = models.AutoField(primary_key=True)
    text_comentari = models.TextField()
    data_comentari = models.DateTimeField()
    nom_usuari_escalador = models.ForeignKey('Escalador', models.DO_NOTHING, db_column='nom_usuari_escalador')
    nom_via = models.ForeignKey('Via', models.DO_NOTHING, db_column='nom_via')
    nom_sector_via = models.CharField(max_length=255)
    nom_crag_via = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'comentari'


class Crag(models.Model):
    nom = models.CharField(primary_key=True, max_length=255)
    localitzacio = models.TextField(blank=True, null=True)
    descripcio = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'crag'


class Encadenament(models.Model):
    id_intent = models.OneToOneField('Intent', models.DO_NOTHING, db_column='id_intent', primary_key=True)
    temps_ascensio = models.DurationField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'encadenament'


class Escalador(models.Model):
    nom_usuari = models.CharField(primary_key=True, max_length=100)
    contrasenya = models.CharField(max_length=255)
    data_naixement = models.DateField(blank=True, null=True)
    nivell = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'escalador'


class Intent(models.Model):
    id_intent = models.AutoField(primary_key=True)
    tipus_ascensio = models.CharField(max_length=100, blank=True, null=True)
    data_intent = models.DateField()
    nom_usuari_escalador = models.ForeignKey(Escalador, models.DO_NOTHING, db_column='nom_usuari_escalador')
    nom_via = models.ForeignKey('Via', models.DO_NOTHING, db_column='nom_via')
    nom_sector_via = models.CharField(max_length=255)
    nom_crag_via = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'intent'
        constraints = [
            models.UniqueConstraint(
                fields=['nom_usuari_escalador', 'nom_via', 'nom_sector_via', 'nom_crag_via', 'data_intent', 'tipus_ascensio'],
                name='unique_intent_escalador_via_data_tipus'
            )
        ]


class Recomanacio(models.Model):
    id_recomanacio = models.AutoField(primary_key=True)
    puntuacio = models.SmallIntegerField(blank=True, null=True)
    descripcio_recomanacio = models.TextField(blank=True, null=True)
    data_recomanacio = models.DateTimeField()
    nom_usuari_escalador = models.ForeignKey(Escalador, models.DO_NOTHING, db_column='nom_usuari_escalador')
    nom_via = models.ForeignKey('Via', models.DO_NOTHING, db_column='nom_via')
    nom_sector_via = models.CharField(max_length=255)
    nom_crag_via = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'recomanacio'
        constraints = [
            models.UniqueConstraint(
                fields=['nom_usuari_escalador', 'nom_via', 'nom_sector_via', 'nom_crag_via'],
                name='unique_recomanacio_escalador_via'
            )
        ]


class Sector(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    descripcio = models.TextField(blank=True, null=True)
    nom_crag = models.ForeignKey(Crag, models.DO_NOTHING, db_column='nom_crag')

    class Meta:
        managed = False
        db_table = 'sector'
        constraints = [
            models.UniqueConstraint(fields=['nom', 'nom_crag'], name='unique_sector_nom_crag')
        ]


class Via(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    descripcio = models.TextField(blank=True, null=True)
    grau_dificultat = models.CharField(max_length=50, blank=True, null=True)
    estil = models.CharField(max_length=100, blank=True, null=True)
    alcada_aproximada_metres = models.IntegerField(blank=True, null=True)
    equipador = models.CharField(max_length=255, blank=True, null=True)
    data_equipament = models.DateField(blank=True, null=True)
    nom_sector = models.ForeignKey(Sector, models.DO_NOTHING, db_column='nom_sector')
    nom_crag_sector = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'via'
        constraints = [
            models.UniqueConstraint(fields=['nom', 'nom_sector', 'nom_crag_sector'], name='unique_via_nom_sector_crag')
        ]
