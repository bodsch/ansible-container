#!/usr/bin/env bash

FACTS_FILE="/etc/ansible/facts.d/update_container.fact"

if [ -f "${FACTS_FILE}" ]
then

  data=$(bash "${FACTS_FILE}")

  image=$(echo "${data}" | jq -r '.update_needed[] | select(.recreate).image')
  name=$(echo "${data}" | jq -r '.update_needed[] | select(.recreate).name')

  echo ""
  echo "special update hook for:"
  echo "  - ${name}"

fi
