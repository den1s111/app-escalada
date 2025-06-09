# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
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
        unique_together = (('nom_usuari_escalador', 'nom_via', 'nom_sector_via', 'nom_crag_via', 'data_intent', 'tipus_ascensio'),)


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
        unique_together = (('nom_usuari_escalador', 'nom_via', 'nom_sector_via', 'nom_crag_via'),)


class Sector(models.Model):
    pk = models.CompositePrimaryKey('nom', 'nom_crag')
    nom = models.CharField(max_length=255)
    descripcio = models.TextField(blank=True, null=True)
    nom_crag = models.ForeignKey(Crag, models.DO_NOTHING, db_column='nom_crag')

    class Meta:
        managed = False
        db_table = 'sector'
        unique_together = (('nom', 'nom_crag'),)


class Via(models.Model):
    pk = models.CompositePrimaryKey('nom', 'nom_sector', 'nom_crag_sector')
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
        unique_together = (('nom', 'nom_sector', 'nom_crag_sector'),)
