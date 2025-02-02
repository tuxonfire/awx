import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import UnifiedJobTemplate, InventorySource, Inventory, JobTemplate, Project, Organization


@pytest.mark.django_db
def test_implied_organization_subquery_inventory():
    orgs = []
    for i in range(3):
        orgs.append(Organization.objects.create(name='foo{}'.format(i)))
    orgs.append(orgs[0])
    for i in range(4):
        org = orgs[i]
        if i == 2:
            inventory = Inventory.objects.create(name='foo{}'.format(i))
        else:
            inventory = Inventory.objects.create(name='foo{}'.format(i), organization=org)
        inv_src = InventorySource.objects.create(name='foo{}'.format(i), inventory=inventory, source='ec2')
    sources = UnifiedJobTemplate.objects.annotate(test_field=rbac.implicit_org_subquery(UnifiedJobTemplate, InventorySource))
    for inv_src in sources:
        assert inv_src.test_field == inv_src.inventory.organization_id


@pytest.mark.django_db
def test_implied_organization_subquery_job_template():
    jts = []
    for i in range(5):
        if i <= 3:
            org = Organization.objects.create(name='foo{}'.format(i))
        else:
            org = None
        if i <= 4:
            proj = Project.objects.create(name='foo{}'.format(i), organization=org)
        else:
            proj = None
        jts.append(JobTemplate.objects.create(name='foo{}'.format(i), project=proj))
    # test case of sharing same org
    jts[2].project.organization = jts[3].project.organization
    jts[2].save()
    ujts = UnifiedJobTemplate.objects.annotate(test_field=rbac.implicit_org_subquery(UnifiedJobTemplate, JobTemplate))
    for jt in ujts:
        if not isinstance(jt, JobTemplate):  # some are projects
            assert jt.test_field is None
        else:
            if jt.project is None:
                assert jt.test_field is None
            else:
                assert jt.test_field == jt.project.organization_id
