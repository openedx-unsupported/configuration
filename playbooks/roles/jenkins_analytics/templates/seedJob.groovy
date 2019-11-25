/*
  Jenkins Analytics Seed Job DSL template
 */

job('{{ jenkins_seed_job.name }}') {

  description('Creates and configures the analytics task jobs.')

  multiscm {
  {% for scm in jenkins_seed_job.multiscm %}
    {% if scm.url %}
    git {
      remote {
        url('{{ scm.url }}')
        branch("{{ scm.branch | default('master') }}")
        {% if scm.credential_id %}
          credentials('{{ scm.credential_id }}')
        {% endif %}
      }
      extensions {
        {% if scm.dest %}
          relativeTargetDirectory('{{ scm.dest }}')
        {% endif %}
        cleanAfterCheckout()
        pruneBranches()
      }
    }
    {% endif %}
  {% endfor %}
  }
  parameters {
    credentialsParam('MASTER_SSH_CREDENTIAL_ID', {
      defaultValue('{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_ID | default("") }}')
      description('Jenkins Credential with ssh access to EMR resources.')
    })
    credentialsParam('GIT_CREDENTIAL_ID', {
      defaultValue('{{ ANALYTICS_SCHEDULE_SECURE_REPO_CREDENTIAL_ID | default("") }}')
      description('Jenkins Credential with read access to the secure git repos.')
    })
    stringParam('DSL_BRANCH', "{{ ANALYTICS_SCHEDULE_JOBS_DSL_REPO_VERSION | default('master') }}",
      'Branch or version of the DSL repo to checkout and use to generate the jobs.')
    stringParam('SECURE_BRANCH', "{{ ANALYTICS_SCHEDULE_SECURE_REPO_VERSION | default('master') }}",
      'Branch or version of the secure repo to checkout and use to generate the jobs.')
    textParam('COMMON_VARS', "{{ ANALYTICS_SCHEDULE_COMMON_VARS | default('') }}",
      'Set default values for the common job parameters.  Format as YAML or provide YAML file as @path/to/file.yml, ' +
      ' absolute or relative to seed job workpace.')
    {% for task in jenkins_seed_job.analytics_tasks %}
    booleanParam('{{ task.id }}',
      {{ task.enable | ternary('true', 'false') }},
      'Create or update this analytics task job.'
    )
    textParam('{{ task.id }}_EXTRA_VARS',
      "{{ task.extra_vars }}",
      'Default values for the analytics task job parameters.  Format as YAML, or provide YAML file as @path/to/file.yml, absolute or relative to seed job workpace.'
    )
    {% endfor %}
  }
  steps {
    gradle {
      useWrapper(true)
      makeExecutable(false)
      {% for task in jenkins_seed_job.dsl.gradle_tasks %}
      tasks('{{ task }}')
      {% endfor %}
    }
    dsl {
      removeAction('{{ jenkins_seed_job.dsl.removed_job_action }}')
      removeViewAction('{{ jenkins_seed_job.dsl.removed_view_action }}')
      additionalClasspath($/{{ jenkins_seed_job.dsl.additional_classpath }}/$)
      lookupStrategy('SEED_JOB')
      {% for job in jenkins_seed_job.dsl.target_jobs %}
      external('{{ job }}')
      {% endfor %}
    }
  }
  keepDependencies(false)
  disabled(false)
  configure { project ->
      canRoam(true)
  }
}
