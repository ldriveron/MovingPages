//open the json file containing the name of books with known movies
const searchbook = async searchBox => {
    const res = await fetch('../static/books_with_movies.json');
    const books = await res.json();

    //get what user is typing in search box and compare to books in json file
    let fits = books.filter(book => {
        const compare = new RegExp(`^${searchBox}`, 'gi');
        return book.title.match(compare);
    });

    //clear the list whenever the search box is empty
    if (searchBox.length === 0) {
        fits = [];
        suggestions.innerHTML = '';
    }

    //call outputHtml and pass the list of matching books
    outputHtml(fits);
};

//populate the suggestions list
const outputHtml = fits => {
    //keep the list size at a reasonable size
    if (fits.length > 10) {
        fits.length = 10;
    }

    if (fits.length > 0) {
        const complete = fits
        .map(fit => `<form name="main_search" method="POST" action="/">
                    <input type="hidden" name="search" value="${fit.title}">
                    <input type="submit" class="book_suggest" value="${fit.title}">
                   </form>`)
        .join('');

        document.getElementById('suggestions').innerHTML = complete;
    }
};

//listen for the input on the search box and call searchbook method
document.getElementById('search').addEventListener('input', () => searchbook(search.value));