# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Accounts(models.Model):
    acc_id = models.BigIntegerField(blank=True, null=True)
    type = models.CharField(max_length=1, blank=True, null=True)
    balance = models.FloatField(blank=True, null=True)
    owner = models.CharField(max_length=40, blank=True, null=True)
    owner_id = models.IntegerField(blank=True, null=True)
    phone = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'accounts'


class Adreces(models.Model):
    address = models.CharField(primary_key=True, max_length=100)
    phone = models.CharField(unique=True, max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adreces'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


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


class Comptes(models.Model):
    acc_id = models.BigIntegerField(primary_key=True)
    type = models.CharField(max_length=1)
    balance = models.FloatField()

    class Meta:
        managed = False
        db_table = 'comptes'


class Contractes(models.Model):
    pk = models.CompositePrimaryKey('acc_id', 'owner_id')
    acc = models.ForeignKey(Comptes, models.DO_NOTHING)
    owner = models.ForeignKey('Titulars', models.DO_NOTHING)
    owner_0 = models.CharField(db_column='owner', max_length=40)  # Field renamed because of name conflict.

    class Meta:
        managed = False
        db_table = 'contractes'
        unique_together = (('acc', 'owner'),)


class Crag(models.Model):
    nom = models.CharField(primary_key=True, max_length=255)
    localitzacio = models.TextField(blank=True, null=True)
    descripcio = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'crag'


class Descoberts(models.Model):
    acc_id = models.BigIntegerField(primary_key=True)
    balance = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'descoberts'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


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


class Movies(models.Model):
    nom = models.CharField(max_length=255, blank=True, null=True)
    data_publicacio = models.IntegerField(blank=True, null=True)
    director = models.CharField(max_length=255, blank=True, null=True)
    puntuacio = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movies'


class Pets(models.Model):
    nom = models.CharField(max_length=100)
    data_naixement = models.DateField()
    tipus = models.CharField(max_length=40)
    pes = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'pets'


class ProducteProductcategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    pare = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'producte_productcategory'


class ProducteProductcategoryRel(models.Model):
    id = models.BigAutoField(primary_key=True)
    productcategory = models.ForeignKey(ProducteProductcategory, models.DO_NOTHING)
    producttemplate = models.ForeignKey('ProducteProducttemplate', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'producte_productcategory_rel'
        unique_together = (('productcategory', 'producttemplate'),)


class ProducteProducttemplate(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    list_price = models.DecimalField(max_digits=8, decimal_places=2)
    cost_price = models.DecimalField(max_digits=8, decimal_places=2)
    salable = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'producte_producttemplate'


class ProducteProductvariant(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=200)
    template = models.ForeignKey(ProducteProducttemplate, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'producte_productvariant'


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


class Titulars(models.Model):
    owner_id = models.IntegerField(primary_key=True)
    address = models.ForeignKey(Adreces, models.DO_NOTHING, db_column='address')

    class Meta:
        managed = False
        db_table = 'titulars'


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
