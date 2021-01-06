
mfe_deployer
############

Overview
--------

The purpose of this document is to provide an overview of how micro-frontend applications (MFEs) can be deployed using the ansible roles from the edx/configuration repository.

For a generic overview of the specific steps that are required for the deployment, please see the `Developer Documentation`_.

Two ansible roles were created by the community to deploy MFEs using ``edx/configuration``:

- ``mfe``: The ``mfe`` role is the base role for the deployments where a single mfe is cloned, built and set up to be served using nginx from the appserver. This role internally follows the steps for building and deployment of MFEs described in the developer documentation, with the exception that it does not use tubular. Ansible users should not directly use this role, and instead use the ``mfe_deployer`` role.
- ``mfe_deployer``: The ``mfe_deployer`` role is used to deploy several MFEs in a programmatic way. Internally, this role, make a call to the base ``mfe`` role for each MFE that is intended to be deployed.

Configuration & Deployment
--------------------------

When running this role, you'll need to set the following variables:

- ``MFES``: list that contains each one of the MFEs that will be deployed. Each MFE should contain a *name* and a *repo*. Optionally, the extra parameters below can be defined for each MFE:
        - **name** (required): The name of the MFE. This is used to define the subdomain in where the MFE is going to be deployed if we are using subdomain deployments.
        - **repo** (required): The name of the repository that is going to be deployed.
        - **node_version**: To indicate which is the version of the node used to build the MFE, by default it takes the value of ``MFE_DEPLOY_NODE_VERSION``.
        - **git_protocol**: To indicate which is the protocol used to clone the repo, by default it takes the value of ``MFE_DEPLOY_GIT_PROTOCOL``.
        - **git_domain**: To indicate which is the domain of the git repository. By default it takes the value of ``MFE_DEPLOY_GIT_DOMAIN``.
        - **git_path**: To indicate the git path of the MFE. By default, it takes the value of ``MFE_DEPLOY_GIT_PATH``.
        - **version**: To indicate the version of the MFE that will be used. By default, it takes the value of ``MFE_DEPLOY_VERSION``.
        - **git_identity**: To indicate the git identity used to clone the repository, by default it takes the value of ``MFE_DEPLOY_GIT_IDENTITY``.
        - **npm_overrides**: To indicate the list of npm overrides that will be installed. Used for branding, See the `Developer Documentation`_ for more details. By default it takes the value of ``MFE_DEPLOY_NPM_OVERRIDES``.
        - **env_extra**: To define custom environment variables that will be used to build this MFE. By default it takes the value of ``MFE_DEPLOY_ENVIRONMENT_EXTRA``.
        - **public_path**: To define the path where the MFE will be deployed. This requires that the MFEs have compatibility with deployments in subdirectories. Regarding to the openedx ecosystem this means that the MFE should be using frontend-build>=1.3.2 and frontend-platform>=1.6.1. By default it takes the value of ``MFE_DEPLOY_PUBLIC_PATH``.
        - **site_name**: Used to define the Environment SITE_NAME, used to build the MFE. By default it takes the value of ``MFE_DEPLOY_SITE_NAME``.
        - **standalone_nginx**: To indicate if the MFE will be deployed in a separated nginx file or if it will be in a shared nginx file with the other MFEs, by default it takes the value of ``MFE_DEPLOY_STANDALONE_NGINX``.

Deployment using subdirectories
_______________________________

By default ``MFE_DEPLOY_STANDALONE_NGINX`` is false, which means that all the microfrontends defined in the ``MFES`` configuration will be deployed to different ``public_path``'s under the same domain (specifically, ``MFE_DEPLOY_COMMON_HOSTNAME``).

.. code-block:: yaml

    MFES:
      - name: profile
        repo: frontend-app-profile
        public_path: "/profile/"
      - name: gradebook
        repo: frontend-app-gradebook
        public_path: "/gradebook/"
      - name: account
        repo: frontend-app-account
        public_path: "/account/"

    ### edxapp Configurations
    ### See comprehensive example below


Please make sure that ``public_path`` starts and ends with a '/', and check that the ``public_path`` configuration is unique for each microfrontends if ``MFE_DEPLOY_STANDALONE_NGINX`` is false.

If we are deploying using subdirectories, it is necessary to set the ``MFE_BASE`` with the shared domain for the microfrontends.

Deployment using subdomains
___________________________

If we want to deploy the microfrontends in different subdomains, we should turn on the ``MFE_DEPLOY_STANDALONE_NGINX``. As an example, this configurations are enough to deploy the profile, gradebook and account microfrontends in a different subdomain.

.. code-block:: yaml

    MFES:
      - name: profile
        repo: frontend-app-profile
      - name: gradebook
        repo: frontend-app-gradebook
      - name: account
        repo: frontend-app-account

    MFE_DEPLOY_STANDALONE_NGINX: true

    ### edxapp Configurations
    ### See comprehensive example below

The domain used for each one of these MFEs, is defined in ``MFE_HOSTNAME``. The default value of that configuration is:

.. code-block:: yaml

    MFE_HOSTNAME: '~^((stage|prod)-)?{{ MFE_NAME }}.*'

Custom configurations
_____________________

As described previously, the compilation of the MFEs is done in the ``mfe`` role, so some configurations cannot be overridden from ``mfe_deployer``. You can see the list of all the default environment configuration in the defaults of the ``mfe`` role. The following variables can be overridden for all MFEs, but not individually: ``MFE_MARKETING_SITE_BASE_URL``, ``MFE_ENTERPRISE_MARKETING_UTM_SOURCE``, ``MFE_ENTERPRISE_MARKETING_UTM_CAMPAIGN``, and ``MFE_ENTERPRISE_MARKETING_FOOTER_UTM_MEDIUM`` for configuration related to the marketing site and ``MFE_NEW_RELIC_APP_ID`` and ``MFE_NEW_RELIC_LICENSE_KEY`` in order to configure the newrelic integration. The default environment variables are defined in the `MFE_ENVIRONMENT_DEFAULT`_ configuration.

LMS Configuration
_________________

The deployment of the MFEs to the appservers will not be enough to have them working properly. Most of them require communication with the LMS, so it is necessary to configure the LMS to accept communication from the MFEs.

The principal configurations that are needed in ansible are: ``EDXAPP_CORS_ORIGIN_WHITELIST``, ``EDXAPP_CSRF_TRUSTED_ORIGINS``, ``EDXAPP_LOGIN_REDIRECT_WHITELIST``. 
They should contain the domain of the MFEs so that the LMS accepts their requests.

It is also necessary to enable the features ENABLE_CORS_HEADERS and ENABLE_CROSS_DOMAIN_CSRF_COOKIE. They can be enabled in Koa with ``EDXAPP_ENABLE_CORS_HEADERS``, ``EDXAPP_ENABLE_CROSS_DOMAIN_CSRF_COOKIE``.

It is also necessary to have configured JWT properly in the LMS. You can use the generate_jwt_signing_key command to generate the signing key. See `decision record about asymmetric JWT`_ for more details.

For each MFE, it might be certain configurations that also need to be changed according to the URLs of the MFE, for instance, for the gradebook, profile and account MFE we need to set ``EDXAPP_LMS_WRITABLE_GRADEBOOK_URL``, ``EDXAPP_PROFILE_MICROFRONTEND_URL`` and ``EDXAPP_ACCOUNT_MICROFRONTEND_URL`` with their respective URLs.

Comprehensive Example of a deployment using subdirectories
__________________________________________________________

.. code-block:: yaml

  MFE_BASE: "mfe.{{ EDXAPP_LMS_BASE }}"

  MFES:
    - name: profile
      repo: frontend-app-profile
      public_path: "/profile/"
    - name: gradebook
      repo: frontend-app-gradebook
      public_path: "/gradebook/"
    - name: account
      repo: frontend-app-account
      public_path: "/account/"

  MFE_DEPLOY_STANDALONE_NGINX: false
  MFE_DEPLOY_COMMON_HOSTNAME: '{{ MFE_BASE }}'
  
  ## edxapp Configurations

  EDXAPP_SESSION_COOKIE_DOMAIN: ".{{ EDXAPP_LMS_BASE }}"
  EDXAPP_CSRF_COOKIE_SECURE: true
  EDXAPP_SESSION_COOKIE_SECURE: true
  EDXAPP_ENABLE_CORS_HEADERS: true
  EDXAPP_ENABLE_CROSS_DOMAIN_CSRF_COOKIE: true
  EDXAPP_CROSS_DOMAIN_CSRF_COOKIE_DOMAIN: ".{{ EDXAPP_LMS_BASE }}"
  EDXAPP_CROSS_DOMAIN_CSRF_COOKIE_NAME: "cross-domain-cookie-mfe"

  EDXAPP_CORS_ORIGIN_WHITELIST:
    - "{{ EDXAPP_CMS_BASE }}"
    - "{{ MFE_BASE }}"

  EDXAPP_CSRF_TRUSTED_ORIGINS:
    - "{{ MFE_BASE }}"

  EDXAPP_LOGIN_REDIRECT_WHITELIST:
    - "{{ EDXAPP_CMS_BASE }}"
    - "{{ MFE_BASE }}"

  # MFE Links
  EDXAPP_LMS_WRITABLE_GRADEBOOK_URL: 'https://{{ MFE_BASE}}/gradebook'
  EDXAPP_PROFILE_MICROFRONTEND_URL: 'https://{{ MFE_BASE}}/profile/u/'
  EDXAPP_ACCOUNT_MICROFRONTEND_URL: 'https://{{ MFE_BASE}}/account'

.. _decision record about asymmetric JWT: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0008-use-asymmetric-jwts.rst
.. _Developer Documentation: https://edx.readthedocs.io/projects/edx-developer-docs/en/latest/developers_guide/micro_frontends_in_open_edx.html#overriding-brand-specific-elements
.. _MFE_ENVIRONMENT_DEFAULT: https://github.com/edx/configuration/blob/master/playbooks/roles/mfe/defaults/main.yml#L95
