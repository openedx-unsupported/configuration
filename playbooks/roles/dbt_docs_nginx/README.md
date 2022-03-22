### Configurations for provisioning the dbt docs server

### Main role:
This is the main role that defines all the tasks necessary for provisioning the dbtdocs server. It is used by the `deploy_nginx_for_dbt_docs.yml` playbook.

### Dependencies:
This role uses the `aws`, `aws_cloudwatch_agent` and `nginx` as dependencies. Therefore, it uses all the default values of those roles.

### Variables:
The only variable that this role requires is `hostname_variable`, which is the string hostname value that comes before `.edx.org`. For instance, to provision the server for the full hostname `hello.world.edx.org`, then set `hostname_variable` to `hello.world`.
