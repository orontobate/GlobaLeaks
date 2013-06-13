#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

usage()
{
cat << EOF
usage: ./${SCRIPTNAME} options

OPTIONS:
   -h      Show this message
   -v      To build a tagged release
   -n      To build a non signed package
   -y      Assume 'yes' to all questions

EOF
}

SIGN=1
while getopts “yhv:n” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    v)
      TAG=$OPTARG
      ;;
    n)
      SIGN=0
      ;;
    y)
      AUTOYES=1
      ;;
    ?)
      usage
      exit
      ;;
    esac
done

auto_setup_env()
{
  cd ${BUILD_DIR}
  if [ -d ${GLBACKEND_TMP} ]; then
    echo "[+] Removing ${GLBACKEND_TMP}"
    rm -rf ${GLBACKEND_TMP}
  fi
  if [ -d ${GLBACKEND_DIR} ]; then
    echo "[+] Copying existent ${GLBACKEND_DIR} in ${GLBACKEND_TMP}"
    cp ${GLBACKEND_DIR} ${GLBACKEND_TMP} -r
  else
    echo "[+] Cloning GLBackend in ${GLBACKEND_TMP}"
    git clone $GLBACKEND_GIT_REPO ${GLBACKEND_TMP}
  fi
}

interactive_setup_env()
{
  cd ${BUILD_DIR}
  if [ -d ${GLBACKEND_TMP} ]; then
    echo "Directory ${GLBACKEND_TMP} already present and need to be removed"
    read -n1 -p "Do you want to delete ${GLBACKEND_TMP}? (y/n): "
    echo
    if [[ $REPLY != [yY] ]]; then
      echo "Cannot proceed"
      exit
    fi
    rm -rf ${GLBACKEND_TMP}
  fi
  if [ -d ${GLBACKEND_DIR} ]; then
    echo "Directory ${GLBACKEND_DIR} already present. Can be used as package source"
    read -n1 -p "Do you want to use the existing repository from ${GLBACKEND_DIR} (y/n): "
    echo
    if [[ $REPLY != [yY] ]]; then
      echo "[+] Cloning GLBackend in ${GLBACKEND_TMP}"
      git clone $GLBACKEND_GIT_REPO ${GLBACKEND_TMP}
    else
      echo "[+] Copying existent ${GLBACKEND_DIR} in ${GLBACKEND_TMP}"
      cp ${GLBACKEND_DIR} ${GLBACKEND_TMP} -r
      USING_EXISTENT_DIR=1
    fi
  else
    echo "[+] Cloning GLBackend in ${GLBACKEND_TMP}"
    git clone $GLBACKEND_GIT_REPO ${GLBACKEND_TMP}
  fi
}

build_glbackend()
{
  cd ${GLBACKEND_TMP}

  if ! test ${USING_EXISTENT_DIR}; then
    if test $TAG; then
      git checkout $TAG || git checkout HEAD
    fi
  fi

  pip install -r requirements.txt

  unzip ${GLC_BUILD}/*.zip -d ${GLBACKEND_TMP}
  mv ${GLBACKEND_TMP}/glclient* ${GLBACKEND_TMP}/glclient

  echo "[+] Building GLBackend"
  POSTINST=${GLBACKEND_TMP}/debian/postinst
  echo "/etc/init.d/globaleaks start" >> $POSTINST
  echo "# generated by your friendly globaleaks build bot :)" >> $POSTINST
  python setup.py sdist
  echo "[+] Building .deb"

  cd dist
  py2dsc globaleaks-*.tar.gz
  cd deb_dist/globaleaks-*
  rm -rf debian/
  cp -rf ${GLBACKEND_TMP}/debian debian

  if [ $SIGN -eq 1 ]; then
    debuild
  else
    debuild -i -us -uc -b
  fi

  mv ${GLBACKEND_TMP}/dist ${GLB_BUILD}
}

if [ $AUTOYES ]; then
  auto_setup_env
else
  interactive_setup_env
fi
build_glbackend

echo "[+] All done!"
echo ""
echo "GLBackend build is now present in ${GLB_BUILD}"

