import axios from 'axios';

// const getTranslationFor = ({ msgid, defaultLabel }) => {
//   return getTranslationCatalog().then(catalog => {
//     if (!catalog) {
//       return '';
//     }
//     const { data } = catalog;
//     return data[msgid] ? data[msgid] : defaultLabel;
//   });
// };

export const getTranslationCatalog = (domain = 'redturtle.prenotazioni') => {
  const catalogUrl = document
    .querySelector('body')
    .getAttribute('data-i18ncatalogurl');
  if (!catalogUrl) {
    return new Promise(function(resolve) {
      resolve(null);
    });
  }
  let language = document.querySelector('html').getAttribute('lang');
  if (!language) {
    language = 'en';
  }

  return axios({
    method: 'GET',
    url: catalogUrl,
    params: { domain, language },
  })
    .then(({ data }) => {
      return { ...data, language };
    })
    .catch(function(error) {
      // handle error
      console.log(error);
    });
};
