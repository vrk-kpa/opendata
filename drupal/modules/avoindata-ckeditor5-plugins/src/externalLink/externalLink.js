import { Plugin } from 'ckeditor5/src/core';

export default class ExternalLink extends Plugin {
	init() {
		console.log('ExternalLink loaded')
		const editor = this.editor;
		const { model } = editor;

		// `listenTo()` and `editor` are available thanks to `Plugin`.
		// By using `listenTo()` you will ensure that the listener is removed when
		// the plugin is destroyed.
		this.listenTo(editor.data, 'ready', () => {
			const linkCommand = editor.commands.get('link');
			const decorator = linkCommand.manualDecorators.get('linkIsExternal')
			const selection = editor.model.document.selection;

			console.log(decorator)

			// Override default link manual decorator conversion to add an icon after the link
			editor.conversion.for( 'downcast' ).attributeToElement( {
				model: 'linkIsExternal',
				view: ( manualDecoratorValue, { writer, schema }, { item } ) => {
					// Manual decorators for block links are handled e.g. in LinkImageEditing.
					if ( !( item.is( 'selection' ) || schema.isInline( item ) ) ) {
						return;
					}

					if ( manualDecoratorValue ) {
						const element = writer.createAttributeElement( 'a', decorator.attributes, { priority: 5 } );

						if ( decorator.classes ) {
							writer.addClass( decorator.classes, element );
						}

						for ( const key in decorator.styles ) {
							writer.setStyle( key, decorator.styles[ key ], element );
						}

						writer.setCustomProperty( 'link', true, element );

						return element;
					}
				}
			} );

			this.listenTo(linkCommand, 'execute', (evt, params) => {
				const linkIsExternal = params[1]['linkIsExternal']
				console.log(evt)
				console.log(params)
				console.log('linkIsExternal', linkIsExternal)
				console.log('source', evt.source)

				if (linkIsExternal) {
					console.log('external link')
					console.log(editor.model.schema)
					editor.model.change(writer => {
						console.log('foo')
						writer.appendText('test', selection)
					});
				} else {
					console.log('not an external link')
				}
			})
		});
	}

	static get pluginName() {
		return 'ExternalLink';
	}
}