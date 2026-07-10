#!/usr/bin/env bash
#
# Based on https://github.com/holman/dotfiles/blob/master/zsh/zshrc.symlink

# shellcheck source=/dev/null

DF=$HOME/.df

if [ -f ~/.secrets ]; then
  source ~/.secrets
fi

if [ -f ~/.local.bash_profile ]; then
  source ~/.local.bash_profile
fi

all_files=("$DF"/**/*.bash)

# Source all of the path ones first
for file in "${all_files[@]}"
do
  if [[ $file != */path.bash ]]; then
    continue
  fi
  source "$file"
done  

# Then source all .bash files that are not path or completion
for file in "${all_files[@]}"
do
  if [[ $file == */path.bash ]]; then
    continue
  fi
  source "$file"
done

unset DF
unset all_files

# I prefer vi mode for command-line editing
set -o vi
export EDITOR=vim
# aikido-endpoint-ruby-cert-config-start
# Allow Ruby Bundler to trust the SafeChain MITM CA while preserving public roots.
export BUNDLE_SSL_CA_CERT="/Library/Application Support/AikidoSecurity/EndpointProtection/run/endpoint-protection-ruby-combined-ca.pem"
# aikido-endpoint-ruby-cert-config-end
# aikido-endpoint-curl-cert-config-start
# Allow curl and other OpenSSL-linked tools to trust the SafeChain MITM CA while preserving the system roots.
export CURL_CA_BUNDLE="/Library/Application Support/AikidoSecurity/EndpointProtection/run/endpoint-protection-openssl-combined-ca.pem"
# aikido-endpoint-curl-cert-config-end
# aikido-endpoint-cert-config-start
# Allow Node.js tooling to trust the SafeChain MITM CA while preserving public roots.
export NODE_EXTRA_CA_CERTS="/Library/Application Support/AikidoSecurity/EndpointProtection/run/endpoint-protection-node-combined-ca.pem"
# aikido-endpoint-cert-config-end
# aikido-endpoint-pip-cert-config-start
# Allow Python package managers to trust the SafeChain MITM CA while preserving user-provided roots.
export PIP_CERT="/Library/Application Support/AikidoSecurity/EndpointProtection/run/endpoint-protection-pip-combined-ca.pem"
export REQUESTS_CA_BUNDLE="/Library/Application Support/AikidoSecurity/EndpointProtection/run/endpoint-protection-pip-combined-ca.pem"
export POETRY_CERTIFICATES_PYPI_CERT="/Library/Application Support/AikidoSecurity/EndpointProtection/run/endpoint-protection-pip-combined-ca.pem"
export UV_SYSTEM_CERTS=true
# aikido-endpoint-pip-cert-config-end
